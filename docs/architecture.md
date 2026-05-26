# Architecture

## Overview

**Kubernetes AI Analyzer** is a Streamlit web application deployed inside a Kubernetes cluster. It connects directly to the cluster API, queries Prometheus metrics via Grafana, and uses a locally running Ollama LLM to generate analysis and answer questions — with **no data leaving the cluster**.

```
┌─────────────────────────────────────────────────────────────┐
│  ai-local namespace                                         │
│                                                             │
│  ┌──────────────────────────────────────────┐               │
│  │  webui Pod (2 containers)                │               │
│  │                                          │               │
│  │  ┌────────────────┐  ┌───────────────┐   │               │
│  │  │  app.py        │  │ mcp-grafana   │   │               │
│  │  │  Streamlit     │  │ sidecar       │   │               │
│  │  │  :8501         │  │ :8000         │   │               │
│  │  └───────┬────────┘  └──────┬────────┘   │               │
│  │          │                  │            │               │
│  └──────────┼──────────────────┼────────────┘               │
│             │                  │                            │
│    ┌────────▼────────┐ ┌───────▼──────────────┐            │
│    │  Ollama Pod     │ │  Grafana (monitoring) │            │
│    │  :11434         │ │  → Prometheus/Thanos  │            │
│    │  qwen3.5:2b     │ │  → Loki               │            │
│    │  phi3.5         │ │  → Alertmanager       │            │
│    │  qwen3:8b       │ └──────────────────────┘            │
│    └─────────────────┘                                      │
│                                                             │
│    ┌─────────────────────────────────────────┐              │
│    │  Kubernetes API (in-cluster)             │              │
│    │  pods / nodes / events / namespaces     │              │
│    └─────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
         ▲
         │  HTTPS (Traefik ingress)
         │  ai.apps.<cluster>.example.com
         │
       Browser
```

## Components

### webui (Streamlit app)

| File | Role |
|---|---|
| `app.py` | Main application — UI, tabs, streaming AI output |
| `k8s_analyzer.py` | K8s API client, Loki client, GrafanaMCPClient |
| `rancher_client.py` | Rancher Gateway authentication |

**Tabs:**

| Tab | Function |
|---|---|
| 📊 Overview | Cluster summary — nodes, pods, namespaces |
| 🔍 Pod Analysis | Pod list with status, filtering, restart counts |
| 📋 Events | Recent Kubernetes events |
| 🤖 AI Insights | One-click AI analysis of selected topic |
| 💬 AI Chat | Conversational assistant with live cluster context |
| 📜 Logs | Loki / K8s API log viewer |
| 🌐 Egress / Network Test | TCP connectivity test + SNAT IP lookup via Cilium |

### Egress / Network Test

Vytvoří dočasný pod `nettest-<uuid>` (busybox:1.36) v cílovém namespace, spustí TCP test a ověří, že egress policy je aktivní v Cilium BPF.

**SNAT IP lookup — klíčový poznatek:**
`cilium bpf egress list` obsahuje vyplněné Egress IP **pouze na gateway nodu** (label `cilium.io/egress-gateway-node=true`). Na ostatních nodech je Egress IP = `0.0.0.0`. Proto `get_snat_ip()` vždy čte z cilium podu na gateway nodu.

**RBAC požadavky** (ClusterRole `webui-rbac.yaml`):
- `pods` — create, delete (nettest pod)
- `pods/log` — get (čtení logů)
- `pods/exec` — create, get (exec do cilium podu)
- `ciliumegressgatewaypolicies` — get, list, watch
- `nodes` — get, list (lookup gateway node)

#### Testování egress vůči Windows jumphostu (euedcapp0299.dc.ege.ds:443)

Pro ověření, že egress provoz opravdu odchází z clusteru přes správnou SNAT IP, se používá reálný Windows jumphost `euedcapp0299.dc.ege.ds` na portu `443`.

**Krok 1 — Spustit TCP listener na Windows jumphostu**

Na stroji `euedcapp0299.dc.ege.ds` otevři PowerShell a spusť následující skript. Ten začne naslouchat na portu 443 a vypisuje IP adresu každého příchozího spojení:

```powershell
$port = 443
$endpoint = [System.Net.IPAddress]::Any
$listener = New-Object System.Net.Sockets.TcpListener($endpoint, $port)

Write-Host "Spouštím naslouchání na portu $port... (Ukončíš pomocí Ctrl+C)" -ForegroundColor Cyan

try {
    $listener.Start()
    while($true) {
        if ($listener.Pending()) {
            $client = $listener.AcceptTcpClient()
            $remoteIp = $client.Client.RemoteEndPoint.ToString()
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Připojení z IP: $remoteIp" -ForegroundColor Yellow

            # Zavřeme spojení, aby se uvolnil slot pro další pokus
            $client.Close()
        }
        Start-Sleep -Milliseconds 100
    }
}
catch {
    Write-Error "Chyba: $_"
}
finally {
    $listener.Stop()
    Write-Host "Naslouchání zastaveno." -ForegroundColor Red
}
```

> Listener vyžaduje oprávnění pro otevření portu 443. Pokud port blokuje Windows Firewall nebo jiný proces, spusť PowerShell jako administrátor.

**Krok 2 — Spustit test v k8s-ai (Egress / Network Test tab)**

1. Otevři k8s-ai UI a přejdi na záložku **🌐 Egress / Network Test**.
2. Vyber **namespace** aplikace, jejíž egress chceš ověřit.
3. Zadej **Target**: `euedcapp0299.dc.ege.ds`
4. Zadej **Port**: `443`
5. Klikni na **Run Test**.

Aplikace vytvoří dočasný pod `nettest-<uuid>` v daném namespace, provede TCP spojení na zadaný cíl a zároveň přečte SNAT IP z Cilium BPF tabulky na gateway nodu.

**Krok 3 — Ověřit výsledek**

- V PowerShell okně na jumphostu se zobrazí příchozí spojení s **reálnou zdrojovou IP**, např.:
  ```
  [14:23:07] Připojení z IP: 10.211.5.42:54312
  ```
- Tato IP musí souhlasit se **SNAT IP** zobrazenou v k8s-ai UI (pole *Egress IP* / *SNAT IP*).
- Pokud se IP shodují → egress gateway funguje správně a provoz odchází přes definovanou VIP.
- Pokud se IP **neshodují** nebo se na jumphostu nic nezobrazí → zkontroluj `CiliumEgressGatewayPolicy` pro daný namespace a stav gateway nodu.

### mcp-grafana sidecar

Runs alongside `app.py` in the same pod. Provides access to Grafana's HTTP API:
- Prometheus PromQL queries (CPU, memory, top pods)
- Firing alerts from Grafana Alerting
- Datasource discovery

The sidecar itself uses the **streamable-http** MCP transport, but `app.py` communicates with Grafana directly via REST API using `GRAFANA_URL` + `GRAFANA_SERVICE_ACCOUNT_TOKEN` env vars.

### Ollama

Local LLM inference server. No GPU — CPU-only.

| Model | Size | Use case |
|---|---|---|
| `qwen3.5:2b` | 2.7 GB | Fast, default for analysis |
| `phi3.5:latest` | 2.2 GB | Microsoft model, good for structured output |
| `qwen3:8b` | 5.2 GB | Higher quality, slower |

Thinking models (`qwen3.*`) receive `/no_think` prefix to skip internal reasoning chain.

### K8sGPT Operator

Runs automated cluster analysis using the Ollama backend. Results available in the Overview tab.

## Data Flow — AI Chat

```
User types question
        │
        ▼
[Fragment rerun — no full page reload]
        │
        ▼
Cluster context (session_state cache):
  - K8s API: pods, nodes, namespaces, events
  - Grafana API: CPU%, Memory%, top pods, alerts
        │
        ▼
Prompt construction:
  LIVE CLUSTER DATA + question
        │
        ▼
ollama.generate(model, system=AI_SKILL_CHAT, stream=True)
        │
        ▼
Token-by-token streaming → st.empty().markdown()
        │
        ▼
Final response saved to st.session_state.messages
```

## Environment Variables

| Variable | Source | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | Helm | Ollama service URL |
| `GRAFANA_URL` | `values.yaml` → Helm | Grafana service URL |
| `GRAFANA_SERVICE_ACCOUNT_TOKEN` | `values.yaml` → Helm | Grafana SA token |
| `AI_SKILL_INSIGHTS` | ConfigMap (`skills.insights`) | System prompt for AI Insights |
| `AI_SKILL_CHAT` | ConfigMap (`skills.chat`) | System prompt for AI Chat |
| `RANCHER_GATEWAYS` | Helm | Rancher API URLs (comma-separated) |
