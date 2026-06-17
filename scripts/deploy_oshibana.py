#!/usr/bin/env python3
"""Deploy index.html to Vercel via REST API."""
import os, json, urllib.request, base64, hashlib

# Read token from .env
TOKEN = ""
env_path = "/Users/boris_ai/.hermes/profiles/boris/.env"
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith("VERCEL_TOKEN=***            TOKEN = line.split("=", 1)[1].strip().strip('"').strip("'")
            break

if not TOKEN:
    print("ERROR: VERCEL_TOKEN not found")
    exit(1)

PROJECT_DIR = "/Users/boris_ai/.hermes/profiles/boris/projects/oshibana"
FILE_PATH = f"{PROJECT_DIR}/index.html"

headers = {
    "Authorization": f"Bearer ***    "Content-Type": "application/json"
}

# List projects to find/create osibana
req = urllib.request.Request("https://api.vercel.com/v9/projects?limit=20", headers=headers)
with urllib.request.urlopen(req) as resp:
    projects = json.loads(resp.read()).get("projects", [])

osibana = next((p for p in projects if p["name"] == "oshibana"), None)
if not osibana:
    data = json.dumps({"name": "oshibana", "framework": None}).encode()
    req = urllib.request.Request("https://api.vercel.com/v9/projects", data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        osibana = json.loads(resp.read())
    print(f"Project created: {osibana['name']}")

project_id = osibana["id"]
print(f"Project: {project_id}")

# Read file
with open(FILE_PATH, "rb") as f:
    content = f.read()

# Create deployment with file
deploy_data = json.dumps({
    "name": "oshibana",
    "project": project_id,
    "target": "production",
    "files": [{
        "file": "index.html",
        "data": base64.b64encode(content).decode(),
        "encoding": "base64"
    }],
    "projectSettings": {"framework": None}
}).encode()

req = urllib.request.Request(
    "https://api.vercel.com/v13/deployments",
    data=deploy_data, headers=headers, method="POST"
)

try:
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        url = result.get('url', '')
        alias = result.get('alias', [])
        print(f"\n✓ Deployed!")
        print(f"  URL: https://{url}")
        for a in alias:
            print(f"  Alias: https://{a}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"Error: {e.code} — {body[:800]}")