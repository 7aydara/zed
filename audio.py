"""
Zed Voice Assistant — Audio Ducking & TTS
Handles system volume ducking via pycaw and text-to-speech via Kokoro.
"""

from __future__ import annotations

import logging
import struct
import time
import os
from typing import Iterator

import numpy as np
import sounddevice as sd

import config

log = logging.getLogger(__name__)

# ─── Volume Ducking (pycaw) ────────────────────────────────────────────────────

# Store original volumes so we can restore them
_original_volumes: dict[int, float] = {}


def _get_pid() -> int:
    """Return current process ID."""
    return os.getpid()


def duck() -> None:
    """
    Lower the volume of every *other* application to DUCK_VOLUME (20 %).
    Saves original volumes for later restoration.
    """
    global _original_volumes
    _original_volumes.clear()

    try:
        from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume

        current_pid = _get_pid()
        sessions = AudioUtilities.GetAllSessions()

        for session in sessions:
            try:
                volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                # Skip our own process
                if session.Process and session.Process.pid == current_pid:
                    continue
                if session.Process:
                    pid = session.Process.pid
                    _original_volumes[pid] = volume.GetMasterVolume()
                    volume.SetMasterVolume(config.DUCK_VOLUME, None)
                    log.debug("Ducked PID %d → %.0f%%", pid, config.DUCK_VOLUME * 100)
            except Exception as exc:
                log.debug("Skipping session: %s", exc)

        log.info("🔉 Ducked %d application(s) to %.0f%%",
                 len(_original_volumes), config.DUCK_VOLUME * 100)

    except Exception as exc:
        log.warning("Could not duck audio: %s", exc)


def restore() -> None:
    """Restore all ducked applications to their original volumes."""
    global _original_volumes

    if not _original_volumes:
        return

    try:
        from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume

        sessions = AudioUtilities.GetAllSessions()
        restored = 0

        for session in sessions:
            try:
                if session.Process and session.Process.pid in _original_volumes:
                    volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                    original = _original_volumes[session.Process.pid]
                    volume.SetMasterVolume(original, None)
                    restored += 1
                    log.debug("Restored PID %d → %.0f%%",
                              session.Process.pid, original * 100)
            except Exception as exc:
                log.debug("Skipping restore for session: %s", exc)

        log.info("🔊 Restored %d/%d application(s)", restored, len(_original_volumes))
        _original_volumes.clear()

    except Exception as exc:
        log.warning("Could not restore audio: %s", exc)
        _original_volumes.clear()


# ─── Edge TTS (WebSockets + PyGame) ────────────────────────────────────────────

import asyncio
import io
import edge_tts
import pygame

_pygame_initialized = False

def _init_pygame():
    global _pygame_initialized
    if not _pygame_initialized:
        # Hide the pygame welcome message
        os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
        # Standard MP3 playback initialization
        pygame.mixer.init(frequency=24000) 
        _pygame_initialized = True
        log.info("✅ Edge TTS ready")

async def _get_edge_audio_bytes(text: str, voice: str) -> bytes:
    communicate = edge_tts.Communicate(text, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

def speak(text: str, interrupt_event: threading.Event = None) -> None:
    """
    Synthesize *text* via Edge TTS websockets and play it through 
    the PyGame mixer synchronously without disk I/O.
    """
    if not text or not text.strip():
        return

    try:
        _init_pygame()
        
        # Await the MP3 chunk generation
        audio_bytes = asyncio.run(_get_edge_audio_bytes(text, config.EDGE_TTS_VOICE))
        if not audio_bytes:
            return

        # Load raw bytes directly into PyGame
        audio_fp = io.BytesIO(audio_bytes)
        pygame.mixer.music.load(audio_fp, "mp3")
        pygame.mixer.music.play()
        
        # Block to ensure audio fully plays before returning
        while pygame.mixer.music.get_busy():
            if interrupt_event and interrupt_event.is_set():
                log.info("Interrupted speak by wake word! Stopping pygame...")
                pygame.mixer.music.stop()
                break
            time.sleep(0.05)

    except Exception as exc:
        log.error("Edge TTS failed: %s", exc)

def speak_streamed(sentences: Iterator[str], interrupt_event: threading.Event = None) -> None:
    """
    Accept an iterator of sentences and stream them consecutively to Edge TTS.
    """
    for sentence in sentences:
        if interrupt_event and interrupt_event.is_set():
            log.info("Interrupted speak_streamed by wake word!")
            break
        sentence = sentence.strip()
        if sentence:
            log.info("🗣️  %s", sentence)
            speak(sentence, interrupt_event)


# ─── Confirmation Beep ─────────────────────────────────────────────────────────

def play_beep(freq: int = 880, duration: float = 0.15) -> None:
    """Play a short confirmation beep when wake word is detected."""
    try:
        t = np.linspace(0, duration, int(24_000 * duration), dtype=np.float32)
        # Soft sine beep with fade-in/out
        envelope = np.minimum(t / 0.05, 1.0) * np.minimum((duration - t) / 0.05, 1.0)
        beep = 0.8 * np.sin(2 * np.pi * freq * t) * envelope
        sd.play(beep.astype(np.float32), samplerate=24_000)
    except Exception as exc:
        log.debug("Beep failed (non-critical): %s", exc)
