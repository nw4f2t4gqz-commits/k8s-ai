# AI Model Benchmark Results

> **Date:** 2026-03-17
> **Cluster:** `eudrpkbe0001` — Ollama pod `ai-local-ollama` (namespace `ai-local`)
> **Ollama URL:** `http://ai-local-ollama:11434`
> **Method:** `kubectl port-forward svc/ai-local-ollama 11434:11434 -n ai-local`

---

## Test Setup

| Parameter | Value |
|---|---|
| Prompts | 5 (K8s domain) |
| Max tokens | 350 |
| Temperature | 0.1 |
| Top-p | 0.9 |
| Modes tested | `generate` (raw) vs `instruct` (chat template via `chat()` API) |
| Models tested | `Qwen2.5:1.5B`, `llama3.2:1b`, `phi3.5:latest` |

### Test Prompts

| # | Label | Description |
|---|---|---|
| 1 | K8s health | Cluster with 120 Running + 3 Pending + 2 CrashLoopBackOff pods |
| 2 | Pod troubleshoot | CrashLoopBackOff / OOMKilled — root cause + kubectl diagnosis |
| 3 | Events analysis | FailedScheduling × 7, OOMKilled × 5, ImagePullBackOff × 3 |
| 4 | Resource optimization | Node A (CPU 85%, RAM 90%) vs Node B (CPU 20%, RAM 30%) |
| 5 | PromQL explain | `sum(rate(node_cpu_seconds_total{mode!='idle'}[5m])) by (node) / ...` |

---

## Results — Final Ranking

| # | Model | Best Mode | Avg TTFT | Avg Total | tok/s | Avg words |
|---|---|---|---|---|---|---|
| 🥇 | **Qwen2.5:1.5B** | instruct | 0.6s | **32.3s** | 9.1 | 209 |
| 🥈 | llama3.2:1b | instruct | 0.4s | 34.1s | **9.8** | **226** |
| 🥉 | phi3.5:latest | instruct | **0.3s** | 51.8s | 6.9 | 193 |

> **TTFT** = Time To First Token
> **Avg Total** = average total response time per prompt
> **tok/s** = tokens per second (chunks streamed)

---

## Mode Comparison: generate vs instruct

| Model | gen Total | inst Total | gen TTFT | inst TTFT | Improvement |
|---|---|---|---|---|---|
| Qwen2.5:1.5B | 34.3s | 32.3s | 1.0s | 0.6s | ✅ +5.8% faster |
| llama3.2:1b | 34.3s | 34.1s | 0.7s | 0.4s | ✅ +0.6% faster |
| phi3.5:latest | 54.3s | 51.8s | 0.9s | 0.3s | ✅ +4.5% faster |

**Conclusion:** `chat()` API (instruct mode) is better for all three models.
TTFT improvement is significant especially for `phi3.5` (0.9s → 0.3s).

---

## Per-Prompt Detail (generate mode)

| Prompt | Qwen2.5 | llama3.2 | phi3.5 |
|---|---|---|---|
| K8s health | 31.7s / 261w | 43.3s / 223w | 55.4s / 172w |
| Pod troubleshoot | 44.1s / 231w | 34.2s / 218w | 53.9s / 193w |
| Events analysis | 27.3s / 266w | 30.0s / 263w | 37.7s / 209w |
| Resource opt. | 24.8s / 165w | 35.2s / 202w | 50.4s / 157w |
| PromQL explain | 43.3s / 257w | 28.9s / 256w | 74.0s / 225w |

## Per-Prompt Detail (instruct mode)

| Prompt | Qwen2.5 | llama3.2 | phi3.5 |
|---|---|---|---|
| K8s health | 32.5s / 206w | 29.3s / 185w | 42.4s / 183w |
| Pod troubleshoot | 34.2s / 232w | 32.8s / 221w | 49.8s / 165w |
| Events analysis | 42.0s / 257w | 31.6s / 254w | 52.8s / 201w |
| Resource opt. | 11.9s / 94w | 34.9s / 241w | 64.0s / 193w |
| PromQL explain | 40.8s / 254w | 42.1s / 229w | 50.0s / 221w |

---

## Recommendations

### ✅ Default model: `Qwen2.5:1.5B` (instruct)
- **Fastest overall** — 32.3s avg total, smallest footprint (940 MB)
- Consistent performance across all K8s prompt types
- Set as default in `app.py` since 2026-03-17

### Alternative: `llama3.2:1b` (instruct)
- Most detailed answers (226 words avg), only 2s slower
- Best choice when answer quality/completeness is priority
- Smallest TTFT (0.4s avg)

### `phi3.5:latest` — not recommended as default
- 60% slower than Qwen2.5 (51.8s vs 32.3s)
- No quality advantage — fewer words on average
- Keep available for user selection (familiar model)

---

## Previously Tested Models (2026-03-17, session 1)

| Model | Avg Total | Avg TTFT | Avg words | Notes |
|---|---|---|---|---|
| phi4-mini:3.8b | 24.2s | 4.5s | 102 | Fast but very brief answers |
| phi3.5:latest | 51.5s | 2.7s | 196 | Verbose, slow |

> phi4-mini has since been removed from the Ollama instance. phi3.5 retained.

---

## Raw Data

Full per-prompt results available in [`bench_results.json`](../bench_results.json).

Run benchmark again:
```bash
# Start port-forward
kubectl port-forward -n ai-local svc/ai-local-ollama 11434:11434 \
  --kubeconfig /home/jartymyt/kubeconfig/eudrpkbe0001.kubeconfig &

# Run
/home/jartymyt/.venv/bin/python /home/jartymyt/k8s-ai/bench_models.py
```
