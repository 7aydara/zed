# 🤖 Zed — Voice Assistant

A local voice assistant that listens 24/7 for a wake word, transcribes your speech, queries **Ollama** with your Obsidian vault as context, and speaks the response — all while ducking your system audio.

**Fully CPU/AMD compatible — no CUDA required.**

## Architecture

```
listener.py ──→ wake word detected (openwakeword)
main.py     ──→ ducks system audio (pycaw)
listener.py ──→ records + transcribes speech (faster-whisper)
brain.py    ──→ loads recent Obsidian notes + queries Ollama (minimax-m2.5:cloud)
audio.py    ──→ speaks response via Edge TTS
main.py     ──→ restores system audio
brain.py    ──→ logs exchange to vault/Journal/YYYY-MM-DD.md
```

## Prerequisites

- **Python 3.10+**
- **Windows 10/11** (pycaw requires Windows audio APIs)
- **A working microphone**
- **Ollama** installed and running locally

### Install Ollama

1. Download and install from [ollama.com](https://ollama.com)
2. Pull the default model:
   ```bash
   ollama pull minimax-m2.5:cloud
   ```

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

# 5. Ensure Ollama is running
# (Just open the Ollama app or run 'ollama serve' in another terminal)

# 6. Run Zed
python main.py
```

## Configuration

All settings are in `config.py`:

| Setting | Default | Description |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434/api/chat` | Your local Ollama endpoint |
| `OLLAMA_MODEL` | `minimax-m2.5:cloud` | LLM model to use |
| `VAULT_PATH` | `~/Documents/ZedVault` | Path to your Obsidian vault |
| `WAKE_WORD` | `hey_jarvis` | Wake word model name |
| `WAKE_THRESHOLD` | `0.2` | Wake word confidence threshold |
| `DUCK_VOLUME` | `0.1` | Volume level during ducking (10%) |
| `WHISPER_MODEL` | `base` | faster-whisper model size |
| `EDGE_TTS_VOICE` | `en-US-AriaNeural` | Edge TTS voice preset |
| `SILENCE_TIMEOUT` | `2.0` | Seconds of silence before stop recording |

### Obsidian Vault

Zed uses a local folder of `.md` files as its memory. By default this is `~/Documents/ZedVault`. You can either:

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
7. The exchange is logged to your Vault

## File Structure

```
zed/
├── main.py          # Orchestrator — starts threads, manages conversation loop
├── listener.py      # Wake word detection + speech-to-text
├── audio.py         # Volume ducking (pycaw) + TTS (Edge TTS)
├── brain.py         # Ollama LLM + Obsidian vault context
├── mcp_client.py    # MCP client stub (clean async interface)
├── config.py        # All configuration constants
├── requirements.txt # Python dependencies
├── README.md        # This file
├── scripts/         # Infrastructure scripts (init_artifact, bundle_artifact, etc.)
└── skills/          # Custom tool skills (.md files)
```

## Skills & MCP Integration

Zed supports native **Skills** (Markdown-based tools) and **MCP (Model Context Protocol)** servers.
- See `skills/` for examples of terminal-based tools.
- Use `python install_mcp.py --cmd <cmd> --args "<args>"` to import tools from any MCP server.

## Troubleshooting

| Issue | Solution |
|---|---|
| `Ollama connection failed` | Ensure Ollama is running and you have pulled the model |
| Microphone not working | Check Windows Settings → Privacy → Microphone |
| `pyaudio` install fails | `pip install pipwin && pipwin install pyaudio` |
| Audio quality issues | Check `MIC_GAIN` and `SAMPLE_RATE` in `config.py` |
