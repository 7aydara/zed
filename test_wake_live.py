"""
Quick live test: feed mic audio to openwakeword WITH software gain.
Say "Hey Jarvis" into your mic!
"""
import numpy as np
import pyaudio
from openwakeword.model import Model as OWWModel
import time

RATE = 16000
CHUNK = 1280  # 80ms
GAIN = 50.0   # Heavy software gain to compensate for low mic level

pa = pyaudio.PyAudio()

# List ALL input devices
print("=" * 60)
print("  Available INPUT devices:")
print("=" * 60)
for i in range(pa.get_device_count()):
    info = pa.get_device_info_by_index(i)
    if info["maxInputChannels"] > 0:
        marker = " <-- DEFAULT" if i == pa.get_default_input_device_info()["index"] else ""
        print(f"  [{i}] {info['name']} (ch={info['maxInputChannels']}, rate={int(info['defaultSampleRate'])}){marker}")
print()

dev = pa.get_default_input_device_info()
print(f"Using: [{dev['index']}] {dev['name']}")

# Open at 16kHz mono
stream = pa.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK,
)

oww = OWWModel(wakeword_models=["hey_jarvis"])
print(f"Models: {list(oww.models.keys())}")
print()
print("=" * 60)
print(f"  Say 'HEY JARVIS' now! (30 sec test, gain={GAIN}x)")
print("=" * 60)

start = time.time()
max_score = 0.0

while time.time() - start < 30:
    raw = stream.read(CHUNK, exception_on_overflow=False)
    audio_raw = np.frombuffer(raw, dtype=np.int16)
    
    raw_level = int(np.abs(audio_raw).mean())
    
    # Apply software gain
    audio_f = audio_raw.astype(np.float64) * GAIN
    audio_f = np.clip(audio_f, -32768, 32767)
    audio_gained = audio_f.astype(np.int16)
    
    gained_level = int(np.abs(audio_gained).mean())
    peak = int(np.abs(audio_gained).max())
    
    # Feed GAINED audio to openwakeword
    prediction = oww.predict(audio_gained)
    score = prediction.get("hey_jarvis", 0.0)
    
    if score > max_score:
        max_score = score
    
    bar = "#" * min(int(gained_level / 500), 50)
    marker = " *** TRIGGERED! ***" if score >= 0.1 else ""
    print(f"  raw={raw_level:4d} gained={gained_level:5d} peak={peak:5d} | score={score:.4f}{marker}  {bar}")

print(f"\nMax score: {max_score:.4f}")
if max_score >= 0.1:
    print("YES - Wake word detected!")
else:
    print("NO - Wake word NOT detected")
    print()
    print("NEXT STEPS:")
    print("  1. Open Windows Settings > System > Sound > Input")
    print("  2. Select your microphone and set input volume to 100%")
    print("  3. Or try a different microphone")

stream.stop_stream()
stream.close()
pa.terminate()
