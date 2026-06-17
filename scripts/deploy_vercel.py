#!/usr/bin/env python3
"""Deploy to Vercel and disable SSO. Reads VERCEL_TOKEN from env."""
import os, json, urllib.request, base64

TOKEN=os.environ["VERCEL_TOKEN"]
PROJECT_DIR = "/Users/boris_ai/.hermes/profiles/boris/projects/oshibana"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# Find project
req = urllib.request.Request("https://api.vercel.com/v9/projects?limit=20", headers=HEADERS)
with urllib.request.urlopen(req) as resp:
    projects = json.loads(resp.read()).get("projects", [])

proj = next((p for p in projects if p["name"] == "oshibana"), None)
if not proj:
    print("No project found, creating...")
    data = json.dumps({"name": "oshibana"}).encode()
    req = urllib.request.Request("https://api.vercel.com/v9/projects", data=data, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req) as resp:
        proj = json.loads(resp.read())

pid = proj["id"]
print(f"Project: {pid}")

# Disable SSO
if proj.get("ssoProtection"):
    data = json.dumps({"ssoProtection": None}).encode()
    req = urllib.request.Request(f"https://api.vercel.com/v9/projects/{pid}", data=data, headers=HEADERS, method="PATCH")
    with urllib.request.urlopen(req) as resp:
        updated = json.loads(resp.read())
    print(f"SSO disabled: ssoProtection={updated.get('ssoProtection')}")

# Read and deploy
with open(f"{PROJECT_DIR}/index.html", "rb") as f:
    content = f.read()

data = json.dumps({
    "name": "oshibana",
    "project": pid,
    "target": "production",
    "files": [{"file": "index.html", "data": base64.b64encode(content).decode(), "encoding": "base64"}],
    "projectSettings": {"framework": None}
}).encode()

req = urllib.request.Request("https://api.vercel.com/v13/deployments", data=data, headers=HEADERS, method="POST")
try:
    with urllib.request.urlopen(req) as resp:
        r = json.loads(resp.read())
        print(f"URL: https://{r['url']}")
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode()[:500]}")
