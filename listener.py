"""
Zed Voice Assistant — Listener
Wake word detection (openwakeword) + speech-to-text (faster-whisper).
Runs in its own daemon thread.

Captures audio at the mic's native rate/channels and resamples to 16 kHz
mono with software gain for reliable wake-word detection.
"""

from __future__ import annotations

import logging
import struct
import threading
import time
import queue
from collections import deque

import numpy as np
import pyaudio
from scipy.signal import resample_poly
from math import gcd

import config

log = logging.getLogger(__name__)

# ─── Globals ────────────────────────────────────────────────────────────────────

_whisper_model = None


def _get_whisper():
    """Lazy-load the faster-whisper model (heavy, ~1 GB for 'small')."""
    global _whisper_model
    if _whisper_model is None:
        log.info("⏳ Loading faster-whisper (%s, %s, %s)…",
                 config.WHISPER_MODEL, config.WHISPER_COMPUTE, config.WHISPER_DEVICE)
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel(
            config.WHISPER_MODEL,
            device=config.WHISPER_DEVICE,
            compute_type=config.WHISPER_COMPUTE,
        )
        log.info("✅ Whisper ready")
    return _whisper_model


# ─── Audio pipeline ─────────────────────────────────────────────────────────────

class AudioPipeline:
    """Handles native-rate capture → 16 kHz mono conversion with gain."""

    def __init__(self, pa: pyaudio.PyAudio):
        # Auto-detect from default input device if config says 0
        dev = pa.get_default_input_device_info()
        self.native_rate = config.MIC_NATIVE_RATE or int(dev["defaultSampleRate"])
        self.native_ch = config.MIC_NATIVE_CHANNELS or int(dev["maxInputChannels"])
        self.gain = config.MIC_GAIN

        # Resampling ratio
        g = gcd(self.native_rate, config.SAMPLE_RATE)
        self.resample_up = config.SAMPLE_RATE // g
        self.resample_down = self.native_rate // g
        self.need_resample = (self.native_rate != config.SAMPLE_RATE)

        # Native chunk size so we get ~CHUNK_SAMPLES after resample
        self.native_chunk = int(config.CHUNK_SAMPLES * self.native_rate / config.SAMPLE_RATE)

        log.info("🎤 Mic: [%d] %s (native=%dHz, ch=%d)",
                 dev["index"], dev["name"], self.native_rate, self.native_ch)
        log.info("📊 Pipeline: %dHz %dch → %dHz mono (gain=%.1fx, resample=%d/%d)",
                 self.native_rate, self.native_ch, config.SAMPLE_RATE,
                 self.gain, self.resample_up, self.resample_down)

    def convert(self, raw: bytes) -> np.ndarray:
        """Convert raw PCM bytes → int16 numpy at 16 kHz mono with gain."""
        audio = np.frombuffer(raw, dtype=np.int16)

        # Stereo → mono
        if self.native_ch >= 2:
            audio = audio.reshape(-1, self.native_ch).mean(axis=1)

        # Software gain
        audio_f = audio.astype(np.float64) * self.gain
        audio_f = np.clip(audio_f, -32768, 32767)

        # Resample to 16 kHz
        if self.need_resample:
            audio_f = resample_poly(audio_f, self.resample_up, self.resample_down)

        return audio_f.astype(np.int16)


# ─── VAD helper ─────────────────────────────────────────────────────────────────

def _is_speech(audio_chunk: bytes, vad) -> bool:
    """Check if a 16-bit PCM chunk contains speech using webrtcvad."""
    try:
        return vad.is_speech(audio_chunk, config.SAMPLE_RATE)
    except Exception:
        return False


# ─── Recording ──────────────────────────────────────────────────────────────────

def _record_until_silence(stream, vad, pipeline: AudioPipeline) -> np.ndarray | None:
    """
    Record audio from *stream* until SILENCE_TIMEOUT seconds of
    consecutive silence, then return the recording as a float32 numpy array.
    Returns None if nothing meaningful was captured.
    """
    frames: list[bytes] = []
    silence_start: float | None = None
    min_speech_frames = 5  # need at least this many speech frames

    speech_frame_count = 0
    # Use 480 samples per VAD frame (30 ms at 16 kHz) — webrtcvad needs 10/20/30 ms
    vad_frame_size = 480  # 30 ms
    vad_frame_bytes = vad_frame_size * 2  # 16-bit = 2 bytes per sample

    log.info("🎙️  Recording… (speak now)")

    buffer = b""

    while True:
        try:
            raw = stream.read(pipeline.native_chunk, exception_on_overflow=False)
        except Exception as exc:
            log.warning("Mic read error: %s", exc)
            break

        # Convert native audio → 16 kHz mono with gain
        audio_16k = pipeline.convert(raw)
        data = audio_16k.tobytes()

        frames.append(data)
        buffer += data

        # Process buffer in VAD-sized chunks
        while len(buffer) >= vad_frame_bytes:
            vad_chunk = buffer[:vad_frame_bytes]
            buffer = buffer[vad_frame_bytes:]

            if _is_speech(vad_chunk, vad):
                speech_frame_count += 1
                silence_start = None
            else:
                if silence_start is None:
                    silence_start = time.monotonic()
                elif time.monotonic() - silence_start >= config.SILENCE_TIMEOUT:
                    log.info("🔇 Silence detected — stopping recording")
                    break
        else:
            continue
        break  # inner while broke out of the for-loop

    if speech_frame_count < min_speech_frames:
        log.info("Too little speech detected, ignoring")
        return None

    # Convert raw PCM bytes → float32 numpy
    raw = b"".join(frames)
    audio_i16 = np.frombuffer(raw, dtype=np.int16)
    audio_f32 = audio_i16.astype(np.float32) / 32768.0
    return audio_f32


def _transcribe(audio: np.ndarray) -> str:
    """Transcribe a float32 audio array using faster-whisper."""
    model = _get_whisper()
    segments, info = model.transcribe(
        audio,
        beam_size=5,
        vad_filter=True,
    )
    text_parts = [seg.text.strip() for seg in segments]
    transcript = " ".join(text_parts).strip()
    log.info("📝 Transcribed: %s", transcript)
    return transcript


# ─── Main listener loop ────────────────────────────────────────────────────────

def listener_loop(
    wake_event: threading.Event,
    text_queue: queue.Queue,
    stop_event: threading.Event,
    continuous_event: threading.Event = None,
) -> None:
    """
    Main listener function — designed to run in a daemon thread.

    1. Listens for wake word in a loop (if not continuous)
    2. On detection → sets wake_event
    3. Records user speech → transcribes → puts result in text_queue
    """
    import webrtcvad

    # ── Init PyAudio + audio pipeline ────────────────────────────────────────
    pa = pyaudio.PyAudio()
    
    # Try opening at 16kHz mono first to let the OS/PyAudio handle resampling
    try:
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=config.SAMPLE_RATE,
            input=True,
            frames_per_buffer=config.CHUNK_SAMPLES,
        )
        config.MIC_NATIVE_RATE = config.SAMPLE_RATE
        config.MIC_NATIVE_CHANNELS = 1
        log.info("🎤 Opened mic directly at 16000Hz mono (OS resampling)")
    except Exception as e:
        log.warning("Could not open at 16kHz mono: %s. Falling back to native.", e)
        # We will fallback in the pipeline below
        stream = None

    pipeline = AudioPipeline(pa)
    
    if stream is None:
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=pipeline.native_ch,
            rate=pipeline.native_rate,
            input=True,
            frames_per_buffer=pipeline.native_chunk,
        )

    # ── Init VAD ────────────────────────────────────────────────────────────
    vad = webrtcvad.Vad(config.VAD_AGGRESSIVENESS)

    # ── Init openwakeword ───────────────────────────────────────────────────
    log.info("⏳ Loading wake word model (%s)…", config.WAKE_WORD)
    from openwakeword.model import Model as OWWModel
    oww = OWWModel(wakeword_models=[config.WAKE_WORD])
    model_keys = list(oww.models.keys())
    log.info("✅ Wake word model ready — models loaded: %s", model_keys)
    log.info("👂 Listening for '%s' (threshold=%.2f)",
             config.WAKE_WORD, config.WAKE_THRESHOLD)

    frame_count = 0
    try:
        while not stop_event.is_set():
            # ── Continuous Mode Override ──
            if continuous_event and continuous_event.is_set():
                log.info("Continuous mode active, recording immediately...")
                audio_data = _record_until_silence(stream, vad, pipeline)
                if audio_data is not None and len(audio_data) > 0:
                    text_queue.put(_transcribe(audio_data))
                else:
                    text_queue.put("")
                continue

            # ── Phase 1: Listen for wake word ───────────────────────────────
            try:
                raw = stream.read(pipeline.native_chunk, exception_on_overflow=False)
            except Exception as exc:
                log.warning("Mic read error: %s", exc)
                time.sleep(0.1)
                continue

            # Convert native audio → 16 kHz mono with gain
            audio_i16 = pipeline.convert(raw)
            prediction = oww.predict(audio_i16)

            # Debug: log scores every ~1s
            frame_count += 1
            if frame_count % 12 == 0:
                level = int(np.abs(audio_i16).mean())
                scores = {k: f"{v:.3f}" for k, v in prediction.items()}
                log.debug("Mic=%d | Scores=%s", level, scores)

            # Check if any model triggered
            for mdl_name, score in prediction.items():
                if score >= config.WAKE_THRESHOLD:
                    log.info("🔔 Wake word detected! (model=%s, score=%.2f)",
                             mdl_name, score)
                    oww.reset()  # reset so it doesn't re-trigger

                    # Signal the orchestrator
                    wake_event.set()

                    # ── Phase 2: Record + Transcribe ────────────────────────
                    audio_data = _record_until_silence(stream, vad, pipeline)

                    if audio_data is not None and len(audio_data) > 0:
                        transcript = _transcribe(audio_data)
                        text_queue.put(transcript)
                    else:
                        text_queue.put("")  # empty = nothing captured

                    break  # back to wake word listening

    except Exception as exc:
        log.error("Listener crashed: %s", exc, exc_info=True)

    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        log.info("Listener shut down")
