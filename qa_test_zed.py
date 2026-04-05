import os
import sys

# Ensure backend respects the original paths
sys.path.insert(0, os.path.abspath("."))

import brain

def main():
    prompt = (
        "Please use your `read_pdf` skill to read the first 10 pages of 'C:/Users/HP/Desktop/AI_Interests.pdf'. "
        "After reading the contents, please use your `pptx` instructional skill to generate a PowerPoint presentation "
        "summarizing the main points. Save the presentation on my desktop as 'AI_Summary.pptx'."
    )
    
    print("🤖 Prompting Zed's Brain (headless mode)...\n")
    print(f"User: {prompt}\n")
    print("Zed: ", end="", flush=True)
    
    # We don't pass an interrupt event, so it runs fully
    for sentence in brain.think(prompt):
        print(sentence, end=" ", flush=True)
        
    print("\n\n✅ Test Script Completed.")

if __name__ == "__main__":
    main()
