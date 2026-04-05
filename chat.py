import threading
import sys
import logging

# We import config just to make sure things are initialized if needed
import config
import brain
import rag

# Set up simple logging for the chat interface
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(message)s"
)
log = logging.getLogger("zed_chat")

def main():
    print("=" * 56)
    print("  🤖  ZED Text Chat Interface")
    print("=" * 56)
    print(f"  LLM        : Ollama ({config.OLLAMA_MODEL})")
    print(f"  Vault      : {config.VAULT_PATH}")
    print("=" * 56)
    print("Type 'exit' or 'quit' to stop.")
    print("=" * 56)

    # Start RAG background sync
    rag.start_background_sync(interval=60)

    try:
        while True:
            # Read input from the user
            user_input = input("\nYou: ")
            
            # Check for exit commands
            if user_input.strip().lower() in ['exit', 'quit']:
                print("\nGoodbye!")
                break
            
            # Skip empty inputs
            if not user_input.strip():
                continue

            print("Zed: ", end="", flush=True)
            
            # Generate response from brain
            try:
                # brain.think returns a generator yielding sentences
                for sentence in brain.think(user_input):
                    print(sentence, end=" ", flush=True)
                print() # New line after the complete response
            except Exception as e:
                print(f"\n[Error communicating with Brain: {e}]")
                
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
