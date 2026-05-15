"""
Test logiky get_snat_ip parsování egress listu.
Spusť: python test_snat_logic.py
"""
import ipaddress

EGRESS_LIST_SAMPLE = """Source IP       Destination CIDR    Egress IP    Gateway IP
10.35.0.6       10.35.0.0/16        10.38.2.149  Excluded CIDR
10.35.0.6       10.36.0.0/16        10.38.2.149  Excluded CIDR
10.35.0.6       10.38.2.128/26      10.38.2.149  Excluded CIDR
10.35.0.6       0.0.0.0/0           10.38.2.149  10.38.2.21
10.35.0.30      10.35.0.0/16        10.38.7.142  Excluded CIDR
10.35.0.30      10.36.0.0/16        10.38.7.142  Excluded CIDR
10.35.0.30      10.38.7.128/25      10.38.7.142  Excluded CIDR
10.35.0.30      0.0.0.0/0           10.38.7.142  10.38.2.21
10.35.0.38      10.35.0.0/16        10.38.2.143  Excluded CIDR
10.35.0.38      10.36.0.0/16        10.38.2.143  Excluded CIDR
10.35.0.38      10.38.2.128/26      10.38.2.143  Excluded CIDR
10.35.0.38      0.0.0.0/0           10.38.2.143  10.38.2.21
10.35.0.41      10.35
"""

# Simulace node IP lookup (node_name -> internal IP)
NODE_IP_MAP = {
    "czplskxs1201.czplskbe1002.k8s.corp": "10.35.0.38",
    "czplskxs1202.czplskbe1002.k8s.corp": "10.35.0.6",
    "czplskxs1203.czplskbe1002.k8s.corp": "10.35.0.30",
}

def parse_egress_list(egress_output: str, source_filter: str, dest_ip: str) -> str:
    """Nová implementace — filtruje Source IP == source_filter (node IP)"""
    best_prefix = -1
    best_egress_ip = ""
    for line in egress_output.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        if parts[0] == "Source":
            continue
        src_ip = parts[0]
        dest_cidr_str = parts[1]
        egress_ip_candidate = parts[2]
        gateway_val = " ".join(parts[3:])
        if src_ip != source_filter:
            continue
        if "Excluded" in gateway_val:
            continue
        try:
            ipaddress.ip_address(gateway_val.split()[0])
        except ValueError:
            continue
        try:
            network = ipaddress.ip_network(dest_cidr_str, strict=False)
            try:
                target_addr = ipaddress.ip_address(dest_ip)
                matches = target_addr in network
            except ValueError:
                matches = dest_cidr_str == "0.0.0.0/0"
            if matches and network.prefixlen > best_prefix:
                best_prefix = network.prefixlen
                best_egress_ip = egress_ip_candidate
        except Exception:
            continue
    return best_egress_ip


dest = "10.249.78.17"
expected_vip = "10.38.2.143"
ok = True

print("=== Test 1: node_ip=10.35.0.38 (správný node s amach-prod policy) ===")
result = parse_egress_list(EGRESS_LIST_SAMPLE, source_filter="10.35.0.38", dest_ip=dest)
status = "✅ OK" if result == expected_vip else f"❌ FAIL (očekáváno {expected_vip}, dostali {result})"
print(f"  Výsledek: {result} — {status}")
ok = ok and result == expected_vip

print("\n=== Test 2: node_ip z node_name lookup (simulace K8s API) ===")
node_name = "czplskxs1201.czplskbe1002.k8s.corp"
node_ip = NODE_IP_MAP.get(node_name, "")
result = parse_egress_list(EGRESS_LIST_SAMPLE, source_filter=node_ip, dest_ip=dest)
status = "✅ OK" if result == expected_vip else f"❌ FAIL"
print(f"  Node: {node_name} → IP: {node_ip} → egress IP: {result} — {status}")
ok = ok and result == expected_vip

print("\n=== Test 3: nettest pod skončil na jiném nodu (10.35.0.6 = jiná policy) ===")
result = parse_egress_list(EGRESS_LIST_SAMPLE, source_filter="10.35.0.6", dest_ip=dest)
print(f"  Výsledek: {result} — ⚠️  Jiná policy (nettest na wrong nodu, výsledek se liší od VIP)")

print("\n=== Test 4: specifičtější CIDR match (not only 0.0.0.0/0) ===")
# Přidáme specifičtější záznam pro 10.249.0.0/16
EGRESS_WITH_SPECIFIC = EGRESS_LIST_SAMPLE + "10.35.0.38  10.249.0.0/16  10.38.2.143  10.38.2.21\n"
result = parse_egress_list(EGRESS_WITH_SPECIFIC, source_filter="10.35.0.38", dest_ip=dest)
status = "✅ OK (longest prefix win)" if result == expected_vip else f"❌ FAIL"
print(f"  Výsledek: {result} — {status}")
ok = ok and result == expected_vip

print("\n=== Test 5: dest_ip nepatří do žádné sítě mimo 0.0.0.0/0 ===")
result = parse_egress_list(EGRESS_LIST_SAMPLE, source_filter="10.35.0.38", dest_ip="8.8.8.8")
status = "✅ OK (fallback 0.0.0.0/0)" if result == expected_vip else f"❌ FAIL"
print(f"  Výsledek: {result} — {status}")
ok = ok and result == expected_vip

print(f"\n{'='*50}")
print(f"Celkový výsledek: {'✅ VŠECHNY TESTY PROŠLY — bezpečné nasadit' if ok else '❌ TESTY SELHALY — neopravuj před analýzou'}")

import ipaddress

EGRESS_LIST_SAMPLE = """Source IP       Destination CIDR    Egress IP    Gateway IP
10.35.0.6       10.35.0.0/16        10.38.2.149  Excluded CIDR
10.35.0.6       10.36.0.0/16        10.38.2.149  Excluded CIDR
10.35.0.6       10.38.2.128/26      10.38.2.149  Excluded CIDR
10.35.0.6       0.0.0.0/0           10.38.2.149  10.38.2.21
10.35.0.30      10.35.0.0/16        10.38.7.142  Excluded CIDR
10.35.0.30      10.36.0.0/16        10.38.7.142  Excluded CIDR
10.35.0.30      10.38.7.128/25      10.38.7.142  Excluded CIDR
10.35.0.30      0.0.0.0/0           10.38.7.142  10.38.2.21
10.35.0.38      10.35.0.0/16        10.38.2.143  Excluded CIDR
10.35.0.38      10.36.0.0/16        10.38.2.143  Excluded CIDR
10.35.0.38      10.38.2.128/26      10.38.2.143  Excluded CIDR
10.35.0.38      0.0.0.0/0           10.38.2.143  10.38.2.21
10.35.0.41      10.35
"""

def parse_egress_list(egress_output: str, pod_ip: str, dest_ip: str) -> tuple:
    """Aktuální implementace — filtruje Source IP == pod_ip"""
    best_prefix = -1
    best_egress_ip = ""
    for line in egress_output.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        if parts[0] == "Source":
            continue
        src_ip = parts[0]
        dest_cidr_str = parts[1]
        egress_ip_candidate = parts[2]
        gateway_val = " ".join(parts[3:])
        if src_ip != pod_ip:
            continue
        if "Excluded" in gateway_val:
            continue
        try:
            ipaddress.ip_address(gateway_val.split()[0])
        except ValueError:
            continue
        try:
            network = ipaddress.ip_network(dest_cidr_str, strict=False)
            try:
                target_addr = ipaddress.ip_address(dest_ip)
                matches = target_addr in network
            except ValueError:
                matches = dest_cidr_str == "0.0.0.0/0"
            if matches and network.prefixlen > best_prefix:
                best_prefix = network.prefixlen
                best_egress_ip = egress_ip_candidate
        except Exception:
            continue
    return best_egress_ip


def parse_egress_list_by_node_ip(egress_output: str, node_ip: str, dest_ip: str) -> str:
    """Alternativa — filtruje Source IP == node_ip (node kde pod běžel)"""
    best_prefix = -1
    best_egress_ip = ""
    for line in egress_output.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        if parts[0] == "Source":
            continue
        src_ip = parts[0]
        dest_cidr_str = parts[1]
        egress_ip_candidate = parts[2]
        gateway_val = " ".join(parts[3:])
        if src_ip != node_ip:
            continue
        if "Excluded" in gateway_val:
            continue
        try:
            ipaddress.ip_address(gateway_val.split()[0])
        except ValueError:
            continue
        try:
            network = ipaddress.ip_network(dest_cidr_str, strict=False)
            try:
                target_addr = ipaddress.ip_address(dest_ip)
                matches = target_addr in network
            except ValueError:
                matches = dest_cidr_str == "0.0.0.0/0"
            if matches and network.prefixlen > best_prefix:
                best_prefix = network.prefixlen
                best_egress_ip = egress_ip_candidate
        except Exception:
            continue
    return best_egress_ip


# ── Testy ──────────────────────────────────────────────────────────────────
dest = "10.249.78.17"
expected_vip = "10.38.2.143"

print("=== Test 1: pod_ip = registrovaný záznam (10.35.0.38) ===")
result = parse_egress_list(EGRESS_LIST_SAMPLE, pod_ip="10.35.0.38", dest_ip=dest)
print(f"  Výsledek: {result}")
print(f"  {'✅ OK' if result == expected_vip else '❌ FAIL (očekáváno ' + expected_vip + ')'}")

print("\n=== Test 2: pod_ip = NETTEST pod (10.35.0.78) — TIMING BUG ===")
result = parse_egress_list(EGRESS_LIST_SAMPLE, pod_ip="10.35.0.78", dest_ip=dest)
print(f"  Výsledek: '{result}'")
print(f"  {'✅ Správně prázdné (timing issue)' if result == '' else '❌ Nečekané'}")

print("\n=== Test 3: node_ip přístup (10.35.0.38 = node kde amach-prod pody běží) ===")
result = parse_egress_list_by_node_ip(EGRESS_LIST_SAMPLE, node_ip="10.35.0.38", dest_ip=dest)
print(f"  Výsledek: {result}")
print(f"  {'✅ OK' if result == expected_vip else '❌ FAIL'}")

print("\n=== Test 4: node_ip jiného nodu (10.35.0.6 = jiná policy) ===")
result = parse_egress_list_by_node_ip(EGRESS_LIST_SAMPLE, node_ip="10.35.0.6", dest_ip=dest)
print(f"  Výsledek: {result}")
print(f"  {'⚠️  Jiná policy (10.38.2.149) — nettest skončil na špatném nodu' if result == '10.38.2.149' else result}")

print("\n=== Závěr ===")
print("Source IP v egress listu = node IP (NE pod IP)")
print("Fix: předat node_name, zjistit node IP, filtrovat podle node IP")
print("Nebo: integrovat SNAT lookup do run_pod_command zatímco pod Running (pod IP pak v mapě je)")
