#!/usr/bin/env python3
"""
Debug skript pro troubleshooting Rancher proxy připojení.
Použití: python3 debug_connection.py <rancher_url> <access_key> <secret_key> <cluster_id>
Nebo přes env proměnné: RANCHER_URL, RANCHER_ACCESS_KEY, RANCHER_SECRET_KEY, RANCHER_CLUSTER_ID
"""
import sys
import os
import base64
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- credentials z argumentů nebo env ---
if len(sys.argv) == 5:
    RANCHER_URL  = sys.argv[1].rstrip('/')
    ACCESS_KEY   = sys.argv[2]
    SECRET_KEY   = sys.argv[3]
    CLUSTER_ID   = sys.argv[4]
else:
    RANCHER_URL  = os.environ.get('RANCHER_URL', '').rstrip('/')
    ACCESS_KEY   = os.environ.get('RANCHER_ACCESS_KEY', '')
    SECRET_KEY   = os.environ.get('RANCHER_SECRET_KEY', '')
    CLUSTER_ID   = os.environ.get('RANCHER_CLUSTER_ID', '')

if not all([RANCHER_URL, ACCESS_KEY, SECRET_KEY]):
    print("Použití: python3 debug_connection.py <rancher_url> <access_key> <secret_key> [cluster_id]")
    print("  nebo nastavte env: RANCHER_URL, RANCHER_ACCESS_KEY, RANCHER_SECRET_KEY, RANCHER_CLUSTER_ID")
    sys.exit(1)

encoded = base64.b64encode(f"{ACCESS_KEY}:{SECRET_KEY}".encode()).decode()
BASIC_AUTH = f"Basic {encoded}"

SEP = "=" * 70

def ok(msg): print(f"  ✅ {msg}")
def err(msg): print(f"  ❌ {msg}")
def info(msg): print(f"  ℹ️  {msg}")
def warn(msg): print(f"  ⚠️  {msg}")


def raw_get(url, auth_header, label=""):
    """Přímý HTTP GET s daným Authorization headrem."""
    try:
        resp = requests.get(
            url,
            headers={"Authorization": auth_header},
            verify=False,
            timeout=15,
            allow_redirects=True,
        )
        cattle_auth = resp.headers.get('X-Api-Cattle-Auth', 'N/A')
        print(f"    {label} → HTTP {resp.status_code}  X-Api-Cattle-Auth: {cattle_auth}")
        if resp.status_code not in (200, 201):
            try:
                body = resp.json()
                print(f"    Body: {json.dumps(body, indent=6)[:400]}")
            except Exception:
                print(f"    Body: {resp.text[:300]}")
        return resp
    except requests.exceptions.SSLError as e:
        print(f"    SSL chyba: {e}")
    except Exception as e:
        print(f"    Chyba: {e}")
    return None


print(SEP)
print("RANCHER PROXY DEBUG")
print(SEP)
print(f"URL:        {RANCHER_URL}")
print(f"Access Key: {ACCESS_KEY}")
print(f"Cluster ID: {CLUSTER_ID or '(bude zjištěno automaticky)'}")
print()

# ── 1. Test Rancher /v3 ────────────────────────────────────────────────────────
print(f"\n[1] Rancher /v3 API - Basic Auth")
raw_get(f"{RANCHER_URL}/v3", BASIC_AUTH, "Basic")

# ── 2. Seznam clusterů ────────────────────────────────────────────────────────
print(f"\n[2] Seznam clusterů (/v3/clusters)")
resp = raw_get(f"{RANCHER_URL}/v3/clusters", BASIC_AUTH, "Basic")
clusters = []
if resp and resp.status_code == 200:
    data = resp.json()
    clusters = data.get('data', [])
    ok(f"Nalezeno {len(clusters)} clusterů:")
    for c in clusters:
        print(f"       - {c.get('name')} | id={c.get('id')} | state={c.get('state')}")
    if not CLUSTER_ID and clusters:
        CLUSTER_ID = clusters[0]['id']
        info(f"Automaticky vybrán cluster: {CLUSTER_ID}")
else:
    err("Nelze načíst clustery")

if not CLUSTER_ID:
    err("Žádné cluster ID — konec")
    sys.exit(1)

PROXY_URL = f"{RANCHER_URL}/k8s/clusters/{CLUSTER_ID}"

# ── 3. Proxy /version – různé autentizační metody ─────────────────────────────
print(f"\n[3] Rancher proxy /version  ({PROXY_URL}/version)")

# a) Basic Auth (stejný jako Rancher API)
raw_get(f"{PROXY_URL}/version", BASIC_AUTH, "Basic Auth         ")

# b) Bearer token  access_key:secret_key
bearer_raw = f"Bearer {ACCESS_KEY}:{SECRET_KEY}"
raw_get(f"{PROXY_URL}/version", bearer_raw, "Bearer key:secret  ")

# c) Bearer token  access_key (bez secret)
raw_get(f"{PROXY_URL}/version", f"Bearer {ACCESS_KEY}", "Bearer access_key  ")

# ── 4. generateKubeconfig ────────────────────────────────────────────────────
print(f"\n[4] generateKubeconfig  POST /v3/clusters/{CLUSTER_ID}?action=generateKubeconfig")
try:
    resp = requests.post(
        f"{RANCHER_URL}/v3/clusters/{CLUSTER_ID}?action=generateKubeconfig",
        headers={"Authorization": BASIC_AUTH, "Content-Type": "application/json"},
        json={},
        verify=False,
        timeout=20,
    )
    print(f"    HTTP {resp.status_code}  X-Api-Cattle-Auth: {resp.headers.get('X-Api-Cattle-Auth','N/A')}")
    if resp.status_code == 200:
        data = resp.json()
        kc_str = data.get('config', '')
        ok(f"Kubeconfig získán ({len(kc_str)} bytů)")
        # Ukázat token ze získaného kubeconfig
        import yaml as _yaml
        kc = _yaml.safe_load(kc_str)
        for u in kc.get('users', []):
            user_data = u.get('user', {})
            token = user_data.get('token', '')
            has_exec = 'exec' in user_data
            if has_exec:
                warn(f"Kubeconfig obsahuje exec: credentials  → Python klient to neumí!")
                print(f"       exec command: {user_data['exec'].get('command','?')}")
            elif token:
                ok(f"Token: {token[:40]}...")
                # Test tohoto tokenu přímo na proxy
                print(f"\n    Test tokenu z generateKubeconfig na proxy /version:")
                raw_get(f"{PROXY_URL}/version", f"Bearer {token}", "Bearer (gen token) ")
    else:
        try:
            body = resp.json()
            err(f"generateKubeconfig selhalo: {body.get('message','?')}")
        except Exception:
            err(f"generateKubeconfig selhalo: {resp.text[:200]}")
except Exception as e:
    err(f"generateKubeconfig výjimka: {e}")

# ── 5. Test kubernetes Python klienta ─────────────────────────────────────────
print(f"\n[5] kubernetes Python klient (from_rancher)")
try:
    from k8s_analyzer import K8sAnalyzer
    analyzer = K8sAnalyzer.from_rancher(RANCHER_URL, CLUSTER_ID, ACCESS_KEY, SECRET_KEY, verify_ssl=False)
    connected, message = analyzer.test_connection()
    if connected:
        ok(f"test_connection: {message}")
        nodes = analyzer.get_nodes()
        ok(f"Nodes: {len(nodes)}")
        pods = analyzer.get_pods()
        ok(f"Pods: {len(pods)}")
    else:
        err(f"test_connection: {message}")
except Exception as e:
    err(f"K8sAnalyzer.from_rancher výjimka: {e}")

print(f"\n{SEP}")
print("DEBUG HOTOVO")
print(SEP)
