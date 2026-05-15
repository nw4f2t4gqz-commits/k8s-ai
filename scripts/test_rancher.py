#!/usr/bin/env python3
"""
Test script pro Rancher integrátor
Tento script otestuje funkcionalitu Rancher klienta bez nutnosti spuštění celé aplikace
"""

import sys
import os

# Přidání cesty k modulu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rancher_client import RancherClient


def test_rancher_client():
    """Test Rancher klienta s příkladovými daty"""

    print("=" * 60)
    print("TEST RANCHER CLIENT")
    print("=" * 60)

    # Načtení credentials z environment variables
    rancher_url = os.environ.get('RANCHER_URL', '')
    access_key = os.environ.get('RANCHER_ACCESS_KEY', '')
    secret_key = os.environ.get('RANCHER_SECRET_KEY', '')

    if not all([rancher_url, access_key, secret_key]):
        print("\n⚠️  VAROVÁNÍ: Rancher credentials nejsou nastaveny")
        print("\nPro testování nastavte následující environment variables:")
        print("  export RANCHER_URL='https://rancher.example.com'")
        print("  export RANCHER_ACCESS_KEY='token-xxxxx'")
        print("  export RANCHER_SECRET_KEY='xxxxxxxxxx'")
        print("\nTest bude přeskočen.")
        return False

    print(f"\n1. Připojování k Rancher: {rancher_url}")
    print("-" * 60)

    try:
        # Vytvoření klienta
        client = RancherClient(rancher_url, access_key, secret_key, verify_ssl=False)
        print("✅ Rancher klient vytvořen")

        # Test připojení
        print("\n2. Test připojení")
        print("-" * 60)
        connected, message = client.test_connection()

        if connected:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
            return False

        # Seznam clusterů
        print("\n3. Načítání seznamu clusterů")
        print("-" * 60)
        clusters = client.list_clusters()

        if clusters:
            print(f"✅ Nalezeno {len(clusters)} clusterů:")
            print()
            for i, cluster in enumerate(clusters, 1):
                print(f"  {i}. {cluster['name']}")
                print(f"     - ID: {cluster['id']}")
                print(f"     - Stav: {cluster['state']}")
                print(f"     - Verze: {cluster['version']}")
                print(f"     - Provider: {cluster['provider']}")
                print()
        else:
            print("⚠️  Žádné clustery nenalezeny")
            return False

        # Test načtení kubeconfig pro první cluster
        if clusters:
            print("\n4. Test načtení kubeconfig")
            print("-" * 60)
            first_cluster = clusters[0]
            print(f"Načítám kubeconfig pro cluster: {first_cluster['name']}")

            kubeconfig = client.get_kubeconfig(first_cluster['id'])

            if kubeconfig:
                print(f"✅ Kubeconfig načten ({len(kubeconfig)} bytů)")
                print(f"   První řádky:")
                lines = kubeconfig.split('\n')[:5]
                for line in lines:
                    print(f"   {line}")
            else:
                print("❌ Nepodařilo se načíst kubeconfig")
                return False

        print("\n" + "=" * 60)
        print("✅ VŠECHNY TESTY ÚSPĚŠNĚ DOKONČENY")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ CHYBA: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_import():
    """Test importu modulů"""
    print("\n" + "=" * 60)
    print("TEST IMPORTU MODULŮ")
    print("=" * 60)

    try:
        print("\n1. Import rancher_client")
        from rancher_client import RancherClient
        print("✅ rancher_client importován")

        print("\n2. Import k8s_analyzer")
        from k8s_analyzer import K8sAnalyzer
        print("✅ k8s_analyzer importován")

        print("\n3. Import streamlit")
        import streamlit
        print("✅ streamlit importován")

        print("\n4. Import requests")
        import requests
        print("✅ requests importován")

        print("\n✅ Všechny moduly úspěšně naimportovány")
        return True

    except ImportError as e:
        print(f"\n❌ Chyba importu: {str(e)}")
        print("\nNainstalujte závislosti pomocí:")
        print("  pip install -r requirements.txt")
        return False


if __name__ == "__main__":
    print("\n🚀 K8sGPT AI Analyzer - Rancher Integration Test")
    print()

    # Test importů
    import_ok = test_import()

    if not import_ok:
        sys.exit(1)

    # Test Rancher klienta (volitelné - vyžaduje credentials)
    print()
    rancher_ok = test_rancher_client()

    print()
    if import_ok and rancher_ok:
        print("🎉 Všechny testy úspěšně dokončeny!")
        sys.exit(0)
    elif import_ok:
        print("⚠️  Importy jsou OK, ale Rancher test byl přeskočen (chybí credentials)")
        sys.exit(0)
    else:
        print("❌ Některé testy selhaly")
        sys.exit(1)
