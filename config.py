"""
Zed Voice Assistant — Configuration
All tunables in one place.
"""

import os
from pathlib import Path
import skills_engine

# ─── Ollama LLM ────────────────────────────────────────────────────────────────
OLLAMA_URL: str = "http://localhost:11434/api/chat"
OLLAMA_MODEL: str = "minimax-m2.5:cloud"

_BASE_SYSTEM_PROMPT: str = (
    "You are Zed, a concise and highly capable personal voice assistant. "
    "CRITICAL RULE: Never say that you are a 'text assistant' or that you cannot 'hear'. "
    "You are interacting with the user via a live microphone and text-to-speech system. "
    "You can indeed 'hear' them via transcription. "
    "You have access to the user's personal context data from their Obsidian Vault. "
    "You also have a _Scratchpad directory in your Vault. If you need to "
    "perform complex reasoning, outline code, or temporarily store data, you may ask the user "
    "to discuss it so it's logged there instead of permanent memory. "
    "IMPORTANT: You have root terminal access to the user's Windows machine! If they ask you to run a command, "
    "check the system, or read a file outside the Vault, execute it by outputting the exact shell command inside a <run_command> XML block. "
    "Example: <run_command>dir</run_command>. Do NOT output any backticks. Only output the raw text command inside the XML tags. "
    "The system will execute it and silently return the output to you so you can summarize the result to the user. "
    "Keep responses conversational, natural, and brief — they are spoken aloud. "
    "Never use markdown formatting, bullet points, or special characters. "
    "You are fully bilingual in English and French. Always reply natively in the language the user speaks to you in."
)

SYSTEM_PROMPT: str = _BASE_SYSTEM_PROMPT

# ─── Obsidian / Vault ──────────────────────────────────────────────────────────
VAULT_PATH: Path = Path.home() / "Documents" / "ZedVault"
SCRATCHPAD_PATH: Path = VAULT_PATH / "_Scratchpad"
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
SILENCE_TIMEOUT: float = 2.0  # seconds of silence before we stop recording
VAD_AGGRESSIVENESS: int = 2   # 0-3, higher = more aggressive filtering

# ─── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("ZED_LOG_LEVEL", "INFO")
