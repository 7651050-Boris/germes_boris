#!/usr/bin/env python3
"""Deploy index.html to Vercel. Usage: python3 deploy.py <vercel_token>"""
import sys, json, urllib.request, base64, os

TOKEN = sys.argv[1]
PROJECT_DIR = "/Users/boris_ai/.hermes/profiles/boris/projects/oshibana"
FILE = f"{PROJECT_DIR}/index.html"

HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# Find or create project
req = urllib.request.Request("https://api.vercel.com/v9/projects?limit=20", headers=HEADERS)
with urllib.request.urlopen(req) as resp:
    projects = json.loads(resp.read()).get("projects", [])

proj = next((p for p in projects if p["name"] == "oshibana"), None)
if not proj:
    data = json.dumps({"name": "oshibana", "framework": None}).encode()
    req = urllib.request.Request("https://api.vercel.com/v9/projects", data=data, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req) as resp:
        proj = json.loads(resp.read())
    print(f"Project created: {proj['name']}")

print(f"Project ID: {proj['id']}")

# Read file
with open(FILE, "rb") as f:
    content = f.read()

# Deploy
data = json.dumps({
    "name": "oshibana",
    "project": proj["id"],
    "target": "production",
    "files": [{"file": "index.html", "data": base64.b64encode(content).decode(), "encoding": "base64"}],
    "projectSettings": {"framework": None}
}).encode()

req = urllib.request.Request("https://api.vercel.com/v13/deployments", data=data, headers=HEADERS, method="POST")
try:
    with urllib.request.urlopen(req) as resp:
        r = json.loads(resp.read())
        print(f"\nDeployed: https://{r['url']}")
        for a in r.get("alias", []):
            print(f"Alias: https://{a}")
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode()[:500]}")
