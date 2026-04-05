import requests

try:
    print("Testing /api/embeddings")
    res1 = requests.post("http://localhost:11434/api/embeddings", json={"model": "nomic-embed-text", "prompt": "hello"})
    print("Status:", res1.status_code)
    if res1.status_code == 200:
        print("Success:", "embedding" in res1.json())
except Exception as e:
    print(e)
    
try:
    print("Testing /api/embed")
    res2 = requests.post("http://localhost:11434/api/embed", json={"model": "nomic-embed-text", "input": "hello"})
    print("Status:", res2.status_code)
    if res2.status_code == 200:
        print("Success:", "embeddings" in res2.json())
except Exception as e:
    print(e)
