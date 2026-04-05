import sys
sys.path.append(r"c:\Users\HP\Desktop\Zeus - Projets AI\zed")
import rag
import config

try:
    print(rag.get_relevant_notes("what is my name?"))
except Exception as e:
    print(f"Error: {e}")
