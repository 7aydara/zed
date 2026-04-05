"""
Zed Voice Assistant — Configuration
All tunables in one place.
"""

import os
from pathlib import Path

# ─── Ollama LLM ────────────────────────────────────────────────────────────────
OLLAMA_URL: str = "http://localhost:11434/api/chat"
OLLAMA_MODEL: str = "minimax-m2.5:cloud"

SYSTEM_PROMPT: str = (
    "You are Zed, a concise and highly capable personal voice assistant. "
    "CRITICAL RULE: Never say that you are a 'text assistant' or that you cannot 'hear'. "
    "You are interacting with the user via a live microphone and text-to-speech system. "
    "You can indeed 'hear' them via transcription. "
    "You have access to the user's personal context data from their Obsidian Vault. "
    "Keep responses conversational, natural, and brief — they are spoken aloud. "
    "Never use markdown formatting, bullet points, or special characters. "
    "You are fully bilingual in English and French. Always reply natively in the language the user speaks to you in."
)

# ─── Obsidian / Vault ──────────────────────────────────────────────────────────
VAULT_PATH: Path = Path.home() / "Documents" / "ZedVault"
CONTEXT_FILES: int = 10  # number of recent .md files to inject as context

# ─── Wake Word ─────────────────────────────────────────────────────────────────
WAKE_WORD: str = "hey_jarvis"
WAKE_THRESHOLD: float = 0.20

# ─── Audio ─────────────────────────────────────────────────────────────────────
DUCK_VOLUME: float = 0.10  # 20 %
SAMPLE_RATE: int = 16_000
MIC_NATIVE_RATE: int = 0  # 0 = auto-detect from default input device
CHANNELS: int = 1
MIC_NATIVE_CHANNELS: int = 0  # 0 = auto-detect from default input device
CHUNK_SAMPLES: int = 1280  # ~80 ms at 16 kHz (after resampling)
MIC_GAIN: float = 15.0  # software gain multiplier (tuned for Superlux E205U)

# ─── Whisper STT ───────────────────────────────────────────────────────────────
WHISPER_MODEL: str = "base"
WHISPER_COMPUTE: str = "int8"
WHISPER_DEVICE: str = "cpu"

# ─── Edge TTS ──────────────────────────────────────────────────────────────────
EDGE_TTS_VOICE: str = "en-US-AriaNeural"

# ─── Silence / VAD ─────────────────────────────────────────────────────────────
SILENCE_TIMEOUT: float = 1.5  # seconds of silence before we stop recording
VAD_AGGRESSIVENESS: int = 2   # 0-3, higher = more aggressive filtering

# ─── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("ZED_LOG_LEVEL", "DEBUG")
