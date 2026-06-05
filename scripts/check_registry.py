import json
import sys

# Fetch registry endpoint
import urllib.request

url = "http://127.0.0.1:8000/registry/remote"
with urllib.request.urlopen(url) as response:
    data = json.loads(response.read().decode())

print("Sections:", list(data["sections"].keys()))
print("Sync:", data["metadata"]["sync_status"])
print("Loaded:", data["metadata"]["sections_loaded"])
print("Failed:", data["metadata"]["sections_failed"])
print("Registry URL:", data["metadata"]["registry_url"])
