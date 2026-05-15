#!/usr/bin/env python3
"""
Test script pro debug Rancher kubeconfig generování
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rancher_client import RancherClient

# Načtení credentials
rancher_url = os.environ.get('RANCHER_URL', '')
access_key = os.environ.get('RANCHER_ACCESS_KEY', '')
secret_key = os.environ.get('RANCHER_SECRET_KEY', '')

if not all([rancher_url, access_key, secret_key]):
    print("Nastavte RANCHER_URL, RANCHER_ACCESS_KEY, RANCHER_SECRET_KEY")
    sys.exit(1)

print("=" * 80)
print("RANCHER KUBECONFIG DEBUG TEST")
print("=" * 80)

# Vytvoření klienta
client = RancherClient(rancher_url, access_key, secret_key, verify_ssl=False)

# Test připojení
print("\n1. Test připojení k Rancher")
connected, message = client.test_connection()
print(f"   Status: {'✅' if connected else '❌'} {message}")

if not connected:
    sys.exit(1)

# Seznam clusterů
print("\n2. Načítání clusterů")
clusters = client.list_clusters()
print(f"   Nalezeno: {len(clusters)} clusterů")

if not clusters:
    print("   Žádné clustery!")
    sys.exit(1)

# Zobrazit první cluster
first_cluster = clusters[0]
print(f"\n3. První cluster:")
print(f"   ID: {first_cluster['id']}")
print(f"   Name: {first_cluster['name']}")
print(f"   State: {first_cluster['state']}")

# Pokusit se získat kubeconfig
print(f"\n4. Generování kubeconfig pro cluster: {first_cluster['name']}")
print("   URL:", f"{rancher_url}/v3/clusters/{first_cluster['id']}?action=generateKubeconfig")

try:
    # Ruční request pro debug
    import requests
    import base64
    
    auth_string = f"{access_key}:{secret_key}"
    encoded = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded}',
        'Content-Type': 'application/json'
    }
    
    # POST request
    response = requests.post(
        f"{rancher_url}/v3/clusters/{first_cluster['id']}?action=generateKubeconfig",
        json={},
        headers=headers,
        verify=False,
        timeout=30
    )
    
    print(f"   HTTP Status: {response.status_code}")
    print(f"   Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Response keys: {list(data.keys())}")
        
        if 'config' in data:
            kubeconfig = data['config']
            print(f"   ✅ Kubeconfig získán ({len(kubeconfig)} bytů)")
            
            # Zkontrolovat obsah
            if 'token' in kubeconfig.lower():
                print("   ✅ Kubeconfig obsahuje token")
            if 'certificate-authority-data' in kubeconfig.lower():
                print("   ✅ Kubeconfig obsahuje CA data")
            
            # Uložit pro inspekci
            with open('/tmp/rancher_kubeconfig.yaml', 'w') as f:
                f.write(kubeconfig)
            print("   📝 Kubeconfig uložen do /tmp/rancher_kubeconfig.yaml")
            
            # Zobrazit první řádky
            print("\n   První řádky kubeconfig:")
            for line in kubeconfig.split('\n')[:10]:
                print(f"   {line}")
        else:
            print(f"   ❌ Klíč 'config' nebyl nalezen")
            print(f"   Response: {json.dumps(data, indent=2)[:500]}")
    else:
        print(f"   ❌ Chyba: {response.text}")
        
except Exception as e:
    print(f"   ❌ Exception: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
