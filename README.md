# 🤖 Zed — Voice Assistant

A local voice assistant that listens 24/7 for a wake word, transcribes your speech, queries Gemini 2.0 Flash with your Obsidian vault as context, and speaks the response — all while ducking your system audio.

**Fully CPU/AMD compatible — no CUDA required.**

## Architecture

```
listener.py ──→ wake word detected (openwakeword)
main.py     ──→ ducks system audio (pycaw)
listener.py ──→ records + transcribes speech (faster-whisper)
brain.py    ──→ loads recent Obsidian notes + queries Gemini 2.0 Flash
audio.py    ──→ speaks response via Kokoro TTS
main.py     ──→ restores system audio
brain.py    ──→ logs exchange to vault/Journal/YYYY-MM-DD.md
```

## Prerequisites

- **Python 3.10+**
- **Windows 10/11** (pycaw requires Windows audio APIs)
- **A working microphone**
- **espeak-ng** (required by Kokoro TTS for phoneme generation)

### Install espeak-ng

1. Download the latest `.msi` from [espeak-ng releases](https://github.com/espeak-ng/espeak-ng/releases)
2. Run the installer
3. Make sure `espeak-ng` is on your PATH (the installer usually handles this)

### Get a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com)
2. Create a free API key
3. Set it as an environment variable (see below)

## Setup

```powershell
# 1. Clone / navigate to the project
cd "c:\Users\HP\Desktop\Zeus - Projets AI\zed"

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
.\venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set your Gemini API key
$env:GEMINI_API_KEY = AIzaSyBPP_r5jfBe-Wbzxr6C5ivgoZrplmq8gxs"your-api-key-here"

# 6. Run Zed
python main.py
```

## Configuration

All settings are in `config.py`:

| Setting | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | env var | Your Gemini API key |
| `GEMINI_MODEL` | `gemini-2.0-flash` | LLM model to use |
| `VAULT_PATH` | `~/Documents/ZedVault` | Path to your Obsidian vault |
| `WAKE_WORD` | `hey_jarvis` | Wake word model name |
| `WAKE_THRESHOLD` | `0.5` | Wake word confidence threshold |
| `DUCK_VOLUME` | `0.20` | Volume level during ducking (20%) |
| `WHISPER_MODEL` | `small` | faster-whisper model size |
| `KOKORO_VOICE` | `af_heart` | Kokoro TTS voice preset |
| `SILENCE_TIMEOUT` | `2.0` | Seconds of silence before stop recording |

### Obsidian Vault

Zed uses a local folder of `.md` files as its memory. By default this is `./vault` inside the project. You can either:

1. **Point to your existing Obsidian vault** by changing `VAULT_PATH` in `config.py`
2. **Use the default** — Zed will create `vault/Journal/` and log all conversations there
3. **Open the vault folder in Obsidian** to visualize your conversations with the graph view

## Usage

1. Run `python main.py`
2. Wait for "Zed is ready" message
3. Say **"hey jarvis"** (the wake word)
4. You'll hear a confirmation beep
5. Speak your question
6. Zed will respond via TTS
7. The exchange is logged to `vault/Journal/YYYY-MM-DD.md`

## File Structure

```
zed/
├── main.py          # Orchestrator — starts threads, manages conversation loop
├── listener.py      # Wake word detection + speech-to-text
├── audio.py         # Volume ducking (pycaw) + TTS (Kokoro)
├── brain.py         # Gemini LLM + Obsidian vault context
├── mcp_client.py    # MCP client stub (clean async interface)
├── config.py        # All configuration constants
├── requirements.txt # Python dependencies
├── README.md        # This file
└── vault/           # Obsidian vault (auto-created)
    └── Journal/     # Daily conversation logs
```

## MCP Integration (Future)

`mcp_client.py` exposes a clean async interface:

```python
client = MCPClient()
await client.connect("ws://localhost:8080")
result = await client.call_tool("web_search", {"query": "weather today"})
```

Currently returns stub responses. Replace the internals with a real MCP SDK when ready.

## Troubleshooting

| Issue | Solution |
|---|---|
| `GEMINI_API_KEY is not set` | Set the env var: `$env:GEMINI_API_KEY = "..."` |
| Microphone not working | Check Windows Settings → Privacy → Microphone |
| `espeak-ng` not found | Install it from the releases page and restart your terminal |
| `pyaudio` install fails | `pip install pipwin && pipwin install pyaudio` |
| High CPU usage | Normal on first run (models are loading). Settles after ~30s |
