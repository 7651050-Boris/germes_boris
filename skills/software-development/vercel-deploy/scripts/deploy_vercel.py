#!/usr/bin/env python3
"""Deploy static site to Vercel via REST API. Reads VERCEL_TOKEN from env."""
import os, json, urllib.request, base64

TOKEN=os.env..._DIR = os.getcwd()
FILE = "index.html"

if len(sys.argv) > 1:
    PROJECT_DIR = os.path.abspath(sys.argv[1])
if len(sys.argv) > 2:
    FILE = sys.argv[2]

HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# Find/create project
project_name = os.path.basename(PROJECT_DIR.rstrip("/"))
req = urllib.request.Request("https://api.vercel.com/v9/projects?limit=50", headers=HEADERS)
with urllib.request.urlopen(req) as resp:
    projects = json.loads(resp.read()).get("projects", [])

proj = next((p for p in projects if p["name"] == project_name), None)
if not proj:
    data = json.dumps({"name": project_name, "framework": None}).encode()
    req = urllib.request.Request("https://api.vercel.com/v9/projects", data=data, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req) as resp:
        proj = json.loads(resp.read())
    print(f"Project created: {proj['name']}")
else:
    print(f"Project found: {proj['name']}")

pid = proj["id"]

# Disable SSO if needed
if proj.get("ssoProtection"):
    data = json.dumps({"ssoProtection": None}).encode()
    req = urllib.request.Request(f"https://api.vercel.com/v9/projects/{pid}", data=data, headers=HEADERS, method="PATCH")
    with urllib.request.urlopen(req) as resp:
        updated = json.loads(resp.read())
    print(f"SSO: disabled")

# Read file
file_path = os.path.join(PROJECT_DIR, FILE)
with open(file_path, "rb") as f:
    content = f.read()

# Deploy
data = json.dumps({
    "name": project_name,
    "project": pid,
    "target": "production",
    "files": [{"file": FILE, "data": base64.b64encode(content).decode(), "encoding": "base64"}],
    "projectSettings": {"framework": None}
}).encode()

req = urllib.request.Request("https://api.vercel.com/v13/deployments", data=data, headers=HEADERS, method="POST")
try:
    with urllib.request.urlopen(req) as resp:
        r = json.loads(resp.read())
        print(f"\nDeployed: https://{r['url']}")
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode()[:500]}")
