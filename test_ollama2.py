import requests

try:
    print("Testing /api/tags")
    res = requests.get("http://localhost:11434/api/tags")
    print("Tags:", res.status_code, res.text[:200])
except Exception as e:
    print(e)
    
try:
    print("Testing /v1/embeddings")
    res = requests.post("http://localhost:11434/v1/embeddings", json={"model": "nomic-embed-text", "input": "hello"})
    print("v1/embeddings:", res.status_code, res.text[:200])
except Exception as e:
    print(e)
