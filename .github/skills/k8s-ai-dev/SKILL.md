---
name: k8s-ai-dev
description: 'Vývoj, build a deploy aplikace Kubernetes AI Analyzer (k8s-ai). Použij pro: úpravy app.py / k8s_analyzer.py / translations.py, docker build/push webui image, helm upgrade ai-local na eudrpkbe0001, debug egress/connectivity testu, XLS generátor FW ticketů. Klíčová slova: k8s-ai, webui, ai-local, egress test, nettest pod, Cilium egress, FW ticket, openpyxl.'
argument-hint: 'Co chceš změnit nebo opravit v k8s-ai aplikaci?'
---

# Kubernetes AI Analyzer — vývojový skill

## Přehled projektu

**Cesta**: `/home/jartymyt/k8s-ai/`
**Framework**: Streamlit 1.x, Python 3.12
**Nasazení**: Helm release `ai-local`, namespace `ai-local`, cluster `eudrpkbe0001`
**Aktuální tag**: `v2026-05-15-17` (revision 91)

## Klíčové soubory

| Soubor | Účel |
|--------|------|
| `app/app.py` | Hlavní Streamlit app — 8 tabů, `@st.fragment`, `st.session_state` |
| `app/k8s_analyzer.py` | Backend K8s API wrapper — `K8sAnalyzer`, `from_rancher()`, `run_pod_command()`, `get_snat_ip()` |
| `app/translations.py` | CZ/EN překlady — funkce `t(key, **kwargs)` |
| `helm/values.yaml` | Helm values — `webui.image.tag`, `ollama.image.tag` |
| `app/requirements.txt` | Python dependencies (obsahuje `openpyxl>=3.1.0`) |
| `helm/templates/webui/webui-rbac.yaml` | ClusterRole — oprávnění pro pods, pods/log, pods/exec, ciliumegressgatewaypolicies, nodes |
| `helm/crds/k8sgpt-crds.yaml` | K8sGPT CRDs — nutno aplikovat ručně (`kubectl apply -f`) před prvním Helm install |

## Docker build & push

```bash
cd /home/jartymyt/k8s-ai

# Build (tag formát: v{YYYY-MM-DD}-{NN})
docker build -t central-system-repo.app.corp:10443/9tech/ai/webui:v2026-05-15-XX .

# Push (port 10443 = push port; values.yaml používá 11443 = pull port)
docker push central-system-repo.app.corp:10443/9tech/ai/webui:v2026-05-15-XX

# Aktualizovat tag v values.yaml
sed -i 's/v2026-05-15-OLD/v2026-05-15-XX/' values.yaml
```

## Helm upgrade

```bash
# Vždy použít OBA values soubory — defaults + prostředí-specifický
helm upgrade ai-local /home/jartymyt/k8s-ai/helm \
  --namespace ai-local \
  --kubeconfig /home/jartymyt/kubeconfig/eudrpkbe0001.kubeconfig \
  -f /home/jartymyt/k8s-ai/helm/values.yaml \
  -f /home/jartymyt/k8s-ai/helm/values-eudrpkbe0001.yaml
```

`helm/values.yaml` — generické defaults (v gitu)
`helm/values-eudrpkbe0001.yaml` — prostředí-specifické (NOT v gitu, `.gitignore: helm/values-*.yaml`)

Při každém novém tagu aktualizuj `webui.image.tag` v `helm/values-eudrpkbe0001.yaml`.

## K8sGPT CRDs — důležité!

Helm 3 **neinstaluje CRDs ze subchartů** automaticky. Před prvním `helm install` na novém clusteru:

```bash
helm show crds /home/jartymyt/k8s-ai/charts/k8sgpt-operator-0.2.27.tgz | \
  kubectl apply -f - --kubeconfig <kubeconfig>
```

Nebo použij připravený soubor:
```bash
kubectl apply -f /home/jartymyt/k8s-ai/crds/k8sgpt-crds.yaml --kubeconfig <kubeconfig>
```

## Rancher proxy autentizace

`K8sAnalyzer.from_rancher()` — **kritické**: `api_client.default_headers['authorization']` musí být **lowercase** `authorization` (ne `Authorization`), jinak `ws_client.create_websocket()` Bearer token nerozpozná a WebSocket exec selže s 403.

## Egress / Network Test tab (tab 8)

### Architektura
1. Uživatel zadá `hostname:port` nebo `IP:port`
2. Vytvoří se dočasný pod `nettest-<uuid8>` (busybox:1.36) v daném namespace
3. Test příkaz: TCP test přes `/dev/tcp` nebo `nc`
4. Po dokončení podu se přečte `pod.spec.node_name` a `pod.status.pod_ip`
5. Volá se `get_snat_ip()` — čte egress list z cilium podu **na gateway nodu**
6. Výsledky se uloží do `st.session_state["egress_test_result"]` (persists přes reruns!)

### session_state klíče egress výsledků
```python
st.session_state["egress_test_result"] = {
    "nc_result": str,       # výstup busybox podu
    "is_success": bool,
    "is_fail": bool,
    "target_host": str,
    "target_port": str,
    "selected_ns": str,
    "policies": list,       # CiliumEgressGatewayPolicy objekty
    "actual_ip": str,       # SNAT IP z Cilium (nebo "")
    "pod_ip": str,          # IP nettest podu
    "snat_debug": str,      # debug výstup z get_snat_ip
}
```

### Cilium SNAT lookup — `get_snat_ip()`

**Klíčové poznatky z produkčního ladění:**
- `cilium bpf egress list` obsahuje vyplněnou Egress IP **POUZE na gateway nodu**
- Na ostatních nodech je Egress IP = `0.0.0.0` → nelze číst z libovolného cilium podu!
- Gateway node má label `cilium.io/egress-gateway-node=true`

**Aktuální strategie (v17+):**
1. Najdi gateway node přes `list_node(label_selector="cilium.io/egress-gateway-node=true")`
2. Najdi cilium pod na tomto nodu přes `field_selector=spec.nodeName=<gw_node>`
3. Spusť `cilium bpf egress list` na tomto podu
4. Hledej řádek kde `Egress IP == expected_vip` (VIP z CiliumEgressGatewayPolicy spec) a `Gateway IP` je validní IP (ne "Excluded CIDR")
5. `expected_vip` = `policies[0].spec.egressGateway.egressIP` — předáváno z app.py

**Formát egress listu:**
```
Source IP     Destination CIDR   Egress IP     Gateway IP
10.35.0.38    10.35.0.0/16       10.38.2.143   Excluded CIDR
10.35.0.38    0.0.0.0/0          10.38.2.143   10.38.2.21
```

**Signatura:**
```python
def get_snat_ip(self, pod_ip: str, dest_ip: str, dest_port: str,
                node_name: str = "", expected_vip: str = "") -> tuple[str, str]:
    # Vrací (snat_ip, debug_str)
```

### run_pod_command()

```python
logs, node_name, pod_ip = analyzer.run_pod_command(namespace, command, timeout=40)
```

Vrací tuple `(logs: str, node_name: str, pod_ip: str)`.
- Fáze 1: čeká na Running → čte `pod.status.pod_ip` + `pod.spec.node_name`
- Fáze 2: čeká na Succeeded/Failed → čte logy

## FW Ticket XLS generátor

Funkce `generate_fw_ticket_xls()` v `app.py`:
- Zobrazuje se **pouze** když `is_fail and not is_success`
- Stav perzistuje přes `session_state` → psaní do justification neruší výsledky
- Formát: orange header (FFC000), yellow data (FFFFC0), borders
- Source VLAN: 54 (OT) pokud název policy obsahuje `-ot-`, jinak 59 (IT)
- Translation klíče: `egress_fw_title`, `egress_fw_desc`, `egress_fw_justification`, `egress_fw_btn`, `egress_fw_warn_justification`

## Časté problémy a řešení

| Problém | Řešení |
|---------|--------|
| WebSocket exec 403 | `default_headers['authorization']` musí být lowercase |
| WebSocket exec 400 | Multi-container pod → použít `run_pod_command()` (temp busybox pod) |
| Download button zmizí po psaní | Session_state pattern — výsledky renderovat vně `if run_test:` bloku |
| SNAT IP = prázdná / debug "0.0.0.0" | Cilium egress list čti z **gateway nodu** (label `cilium.io/egress-gateway-node=true`) |
| K8sGPT objekt nenasazen | CRDs ze subchartů Helm neinstaluje — aplikuj ručně přes `kubectl apply` |
| Docker push 403 | Push na port **10443**, `values.yaml` reference na **11443** |

## Verze history

| Tag | Změna |
|-----|-------|
| v2026-05-15-01 | Fix docker push port (10443) |
| v2026-05-15-03 | `exec_in_pod` — `_preload_content=False` fix |
| v2026-05-15-04 | `authorization` lowercase fix |
| v2026-05-15-05 | `run_pod_command` temp pod approach |
| v2026-05-15-06 | openpyxl + `generate_fw_ticket_xls()` + FW ticket UI |
| v2026-05-15-07 | Session_state fix pro download button |
| v2026-05-15-08–10 | SNAT IP pokusy (checkip, nat list, egress list libovolný node — vše špatně) |
| v2026-05-15-11–15 | Postupné opravy egress lookup (node IP, pod IP — stále špatně) |
| v2026-05-15-16 | Nový přístup: hledej `Egress IP == expected_vip` — ale stále libovolný cilium pod |
| v2026-05-15-17 | **Finální fix**: čti egress list z cilium podu na **gateway nodu** (label `cilium.io/egress-gateway-node=true`) |
| v2026-05-15-11 | Přidán `cilium bpf egress list` + debug výstup v expanderu |
