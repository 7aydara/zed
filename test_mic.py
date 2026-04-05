"""Quick mic + wake word test — auto-detects mic, applies gain, resamples."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import time
import numpy as np
import pyaudio
from scipy.signal import resample_poly
from math import gcd
from openwakeword.model import Model as OWWModel

TARGET_RATE = 16_000
TARGET_CHUNK = 1280
GAIN = 5.0
THRESHOLD = 0.3

print("=" * 55)
print("  MIC + WAKE WORD TEST (auto-detect + gain)")
print("=" * 55)

pa = pyaudio.PyAudio()

# Auto-detect mic settings
dev = pa.get_default_input_device_info()
native_rate = int(dev["defaultSampleRate"])
native_ch = int(dev["maxInputChannels"])
native_chunk = int(TARGET_CHUNK * native_rate / TARGET_RATE)

g = gcd(native_rate, TARGET_RATE)
resample_up = TARGET_RATE // g
resample_down = native_rate // g

print(f"\nMic: [{dev['index']}] {dev['name']}")
print(f"Pipeline: {native_rate}Hz {native_ch}ch -> {TARGET_RATE}Hz mono")
print(f"Gain: {GAIN}x | Resample: {resample_up}/{resample_down}")


def convert(raw):
    audio = np.frombuffer(raw, dtype=np.int16)
    if native_ch >= 2:
        audio = audio.reshape(-1, native_ch).mean(axis=1)
    audio_f = audio.astype(np.float64) * GAIN
    audio_f = np.clip(audio_f, -32768, 32767)
    if native_rate != TARGET_RATE:
        audio_f = resample_poly(audio_f, resample_up, resample_down)
    return audio_f.astype(np.int16)


stream = pa.open(
    format=pyaudio.paInt16,
    channels=native_ch,
    rate=native_rate,
    input=True,
    frames_per_buffer=native_chunk,
)

print("\nLoading wake word model...")
oww = OWWModel(wakeword_models=["hey_jarvis"])
print(f"Model loaded. Keys: {list(oww.models.keys())}")
print(f"\nListening... Say 'HEY JARVIS' now! (threshold={THRESHOLD})")
print("(showing processed mic level + scores every ~0.5s)\n")

frame_count = 0
try:
    while True:
        raw = stream.read(native_chunk, exception_on_overflow=False)
        audio_16k = convert(raw)

        level = int(np.abs(audio_16k).mean())
        prediction = oww.predict(audio_16k)

        frame_count += 1
        if frame_count % 6 == 0:
            bars = "#" * min(int(level / 100), 40)
            scores = {k: f"{v:.4f}" for k, v in prediction.items()}
            print(f"  Mic: {level:5d} {bars:40s} | {scores}")

            for name, score in prediction.items():
                if score >= THRESHOLD:
                    print(f"\n  >>> TRIGGERED! {name} = {score:.4f} <<<")
                    oww.reset()

except KeyboardInterrupt:
    print("\n\nStopped.")
finally:
    stream.close()
    pa.terminate()
