"""
Zed Voice Assistant — Main Orchestrator
Starts all threads, manages the conversation loop.
"""

from __future__ import annotations

import logging
import queue
import signal
import sys
import threading
import time

import config

# ─── Logging setup ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s │ %(name)-12s │ %(levelname)-5s │ %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("zed")


def main() -> None:
    """Entry point — run the Zed voice assistant."""

    log.info("=" * 56)
    log.info("  🤖  ZED Voice Assistant")
    log.info("=" * 56)
    log.info("  Wake word  : %s", config.WAKE_WORD)
    log.info("  Whisper    : %s (%s, %s)", config.WHISPER_MODEL,
             config.WHISPER_COMPUTE, config.WHISPER_DEVICE)
    log.info("  LLM        : Ollama (%s)", config.OLLAMA_MODEL)
    log.info("  Vault       : %s", config.VAULT_PATH)
    log.info("=" * 56)

    # Setup Vault dirs
    config.VAULT_PATH.mkdir(parents=True, exist_ok=True)

    # ── Shared state ────────────────────────────────────────────────────────
    wake_event = threading.Event()
    text_queue: queue.Queue[str] = queue.Queue()
    stop_event = threading.Event()

    # ── Import modules (lazy-loads heavy deps internally) ───────────────────
    import audio
    import brain
    from listener import listener_loop

    # ── Start listener thread ───────────────────────────────────────────────
    listener_thread = threading.Thread(
        target=listener_loop,
        args=(wake_event, text_queue, stop_event),
        daemon=True,
        name="listener",
    )
    listener_thread.start()
    log.info("👂 Listener thread started")

    # ── Graceful shutdown ───────────────────────────────────────────────────
    def shutdown(signum=None, frame=None):
        log.info("🛑 Shutting down…")
        stop_event.set()
        audio.restore()  # make sure volumes are back
        time.sleep(0.5)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("DEBUG: Executing lazily loaded imports")
    import listener
    import rag
    print("DEBUG: Importing dream")
    import dream
    print("DEBUG: Pre-loading heavy PyTorch models")
    # Pre-load heavy PyTorch models in the background so the first turn is instant
    threading.Thread(target=listener._get_whisper, daemon=True).start()
    threading.Thread(target=audio._init_pygame, daemon=True).start()
    
    print("DEBUG: Starting RAG sync")
    # ── Start Background Workers ─────────────────────────────────────────────
    rag.start_background_sync(interval=60)
    print("DEBUG: Starting dream thread")
    dream.start_background_dream(interval=3600)  # Consolidate memory every hour

    print("DEBUG: Reaching main conversation loop")
    # ── Main conversation loop ──────────────────────────────────────────────
    log.info("✅ Zed is ready — say '%s' to start!", config.WAKE_WORD.replace("_", " "))

    try:
        while not stop_event.is_set():
            # Wait for wake word detection
            wake_event.wait(timeout=1.0)
            if not wake_event.is_set():
                continue  # timeout, just loop again
            wake_event.clear()

            # Clear any stale items from the text_queue
            while not text_queue.empty():
                try:
                    text_queue.get_nowait()
                except queue.Empty:
                    break

            log.info("🔔 Wake word heard!")

            # Play confirmation beep FIRST (before ducking, so it's loud)
            audio.play_beep()

            # Duck system audio
            audio.duck()

            # Wait for transcription
            try:
                transcript = text_queue.get(timeout=300.0)
            except queue.Empty:
                log.warning("⏰ Timed out waiting for speech")
                audio.restore()
                continue

            if not transcript.strip():
                log.info("🤷 No speech detected, going back to listening")
                audio.restore()
                continue

            log.info("💬 You said: %s", transcript)

            # Get response from brain (streams sentences)
            try:
                sentence_stream = brain.think(transcript, wake_event)
                audio.speak_streamed(sentence_stream, wake_event)
            except Exception as exc:
                log.error("Brain/TTS error: %s", exc)
                audio.speak("Sorry, something went wrong. Please try again.", wake_event)

            # Restore system audio
            audio.restore()

            log.info("👂 Listening for wake word again…\n")

    except KeyboardInterrupt:
        shutdown()
    except Exception as exc:
        log.error("Fatal error: %s", exc, exc_info=True)
        shutdown()


if __name__ == "__main__":
    main()
