"""
Comprehensive wake word diagnostic.
Tests mic levels, openwakeword backend, and model loading.
"""
import sys
import os
import time

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
import pyaudio

RATE = 16000
CHUNK = 1280  # 80ms at 16kHz

print("=" * 60)
print("  ZED WAKE WORD DIAGNOSTIC")
print("=" * 60)

# -- Step 1: Check openwakeword backend --
print("\n[1/5] Checking inference backend...")
try:
    import tflite_runtime
    print("  OK: tflite_runtime available")
except ImportError:
    print("  WARN: tflite_runtime NOT installed -- using onnxruntime fallback")
    try:
        import onnxruntime
        print(f"  OK: onnxruntime version: {onnxruntime.__version__}")
    except ImportError:
        print("  FAIL: NEITHER tflite_runtime NOR onnxruntime installed!")
        print("     Install one: pip install onnxruntime")
        sys.exit(1)

# -- Step 2: List microphones --
print("\n[2/5] Scanning audio devices...")
pa = pyaudio.PyAudio()

input_devices = []
for i in range(pa.get_device_count()):
    info = pa.get_device_info_by_index(i)
    if info["maxInputChannels"] > 0:
        input_devices.append(info)
        marker = " <-- DEFAULT" if info["index"] == pa.get_default_input_device_info()["index"] else ""
        print(f"  [{info['index']}] {info['name']} "
              f"(ch={info['maxInputChannels']}, rate={int(info['defaultSampleRate'])}){marker}")

if not input_devices:
    print("  FAIL: No input devices found!")
    pa.terminate()
    sys.exit(1)

default_mic = pa.get_default_input_device_info()
print(f"\n  Using default mic: [{default_mic['index']}] {default_mic['name']}")

# -- Step 3: Test mic levels --
print("\n[3/5] Testing mic levels (5 seconds)...")
print("       SPEAK NOW or make noise!\n")

stream = pa.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK,
)

max_level = 0
levels = []
start = time.time()
while time.time() - start < 5.0:
    raw = stream.read(CHUNK, exception_on_overflow=False)
    audio = np.frombuffer(raw, dtype=np.int16)
    mean_level = int(np.abs(audio).mean())
    peak_level = int(np.abs(audio).max())
    max_level = max(max_level, peak_level)
    levels.append(mean_level)

    bars = "#" * min(int(mean_level / 100), 50)
    print(f"  mean={mean_level:5d}  peak={peak_level:5d}  {bars}")

avg_level = sum(levels) / len(levels) if levels else 0
print(f"\n  Summary: avg_mean={avg_level:.0f}, max_peak={max_level}")

if max_level < 100:
    print("  FAIL: Mic levels are essentially ZERO.")
    print("     -> Check Windows Sound Settings > Input")
    print("     -> Make sure the correct mic is selected")
    print("     -> Try increasing mic volume/boost in Device Properties")
elif max_level < 500:
    print("  WARN: Mic levels are very low. Wake word detection may struggle.")
    print("     -> Try increasing mic volume in Windows Sound Settings")
elif max_level < 2000:
    print("  WARN: Mic levels are low-medium. Try speaking louder or closer to mic.")
else:
    print("  OK: Mic levels look good!")

# -- Step 4: Load wake word model --
print("\n[4/5] Loading openwakeword model...")
from openwakeword.model import Model as OWWModel

# Try loading the model
try:
    oww = OWWModel(wakeword_models=["hey_jarvis"])
    model_keys = list(oww.models.keys())
    print(f"  OK: Model loaded successfully. Keys: {model_keys}")
except Exception as e:
    print(f"  FAIL: Failed to load model: {e}")
    stream.close()
    pa.terminate()
    sys.exit(1)

# Also check what model files are available
print("\n  Checking available pre-trained models...")
try:
    import openwakeword
    oww_path = openwakeword.__path__[0]
    from pathlib import Path
    model_dir = Path(oww_path) / "resources" / "models"
    if model_dir.exists():
        models = list(model_dir.glob("*.onnx")) + list(model_dir.glob("*.tflite"))
        for m in sorted(models):
            print(f"    {m.name} ({m.stat().st_size // 1024} KB)")
    else:
        print(f"    Model dir not found at: {model_dir}")
except Exception as e:
    print(f"    Could not enumerate models: {e}")

# -- Step 5: Live wake word test --
print("\n[5/5] Live wake word test (15 seconds)...")
print("       Say 'HEY JARVIS' clearly into the mic!")
print("       Threshold: 0.3  |  Showing ALL non-zero scores\n")

oww.reset()
frame_count = 0
start = time.time()
detected = False

while time.time() - start < 15.0:
    raw = stream.read(CHUNK, exception_on_overflow=False)
    audio = np.frombuffer(raw, dtype=np.int16)

    prediction = oww.predict(audio)
    frame_count += 1

    # Show every frame's score if non-zero, otherwise show every ~1s
    for name, score in prediction.items():
        if score > 0.01:
            level = int(np.abs(audio).mean())
            triggered = " <<< TRIGGERED!" if score >= 0.3 else ""
            print(f"  [{time.time()-start:5.1f}s] Score={score:.4f}  mic={level}{triggered}")
            if score >= 0.3:
                detected = True
        elif frame_count % 12 == 0:
            level = int(np.abs(audio).mean())
            print(f"  [{time.time()-start:5.1f}s] Score={score:.4f}  mic={level}")

stream.close()
pa.terminate()

print("\n" + "=" * 60)
if detected:
    print("  RESULT: Wake word was successfully detected!")
else:
    print("  RESULT: Wake word was NOT detected in 15 seconds")
    if max_level < 500:
        print("\n  LIKELY CAUSE: Microphone levels too low.")
        print("  FIX: Go to Windows Settings > System > Sound > Input")
        print("       Make sure the correct mic is selected and volume is up.")
    else:
        print("\n  POSSIBLE CAUSES:")
        print("  1. Pronunciation -- try saying 'Hey Jarvis' slowly and clearly")
        print("  2. Model issue -- try lowering threshold (currently 0.3)")
        print("  3. Background noise interfering")
print("=" * 60)
