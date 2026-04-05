import requests
import sys

try:
    print("Pulling nomic-embed-text...")
    res = requests.post("http://localhost:11434/api/pull", json={"model": "nomic-embed-text"}, stream=True)
    for line in res.iter_lines():
        if line:
            print(line.decode('utf-8'))
except Exception as e:
    print(e)
