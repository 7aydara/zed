import sys
sys.path.append(r"c:\Users\HP\Desktop\Zeus - Projets AI\zed")
from brain import _analyze_memory

try:
    _analyze_memory("My name is John and I am building Zed.", "That's great, John!")
except Exception as e:
    print(f"Error: {e}")
