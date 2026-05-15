#!/usr/bin/env python3
"""
Ollama Model Benchmark
- Auto-discovers all available models
- Tests each model in two modes:
    generate  = raw completion (no chat template)
    instruct  = chat() API with proper role-based messages + chat template
- Metrics: TTFT, total time, tok/s, word count
"""

import ollama
import time
import json

OLLAMA_URL = "http://127.0.0.1:11434"

PROMPTS = [
    (
        "K8s health",
        "Analyze this Kubernetes cluster: 5 nodes Ready, 120 pods Running, "
        "3 Pending, 2 CrashLoopBackOff. Summarize health status and top 3 recommendations.",
    ),
    (
        "Pod troubleshoot",
        "Pod 'api-server' in namespace 'prod' is CrashLoopBackOff with OOMKilled exit code. "
        "What are 3 most likely root causes and which kubectl commands would you run to diagnose?",
    ),
    (
        "Events analysis",
        "Recent K8s events: FailedScheduling (insufficient CPU) x7, OOMKilled x5, "
        "ImagePullBackOff x3. What immediate actions should L2 support take?",
    ),
    (
        "Resource optimization",
        "Node A: CPU 85%, RAM 90%, 30 pods. Node B: CPU 20%, RAM 30%, 10 pods. "
        "Recommend resource optimization strategies.",
    ),
    (
        "PromQL explain",
        "Explain what this PromQL measures and how to interpret the result:\n"
        "sum(rate(node_cpu_seconds_total{mode!='idle'}[5m])) by (node) / "
        "sum(rate(node_cpu_seconds_total[5m])) by (node)",
    ),
]

SYSTEM = (
    "You are an expert Kubernetes L2/L3 support engineer. "
    "Be concise, technical and actionable. Use bullet points where appropriate."
)

GEN_OPTIONS = {"num_predict": 350, "temperature": 0.1, "top_p": 0.9}

# ANSI
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"
DIM    = "\033[2m"


def best_color(values, lower_is_better):
    best = min(values) if lower_is_better else max(values)
    return [f"{GREEN}{v}{RESET}" if v == best else str(v) for v in values]


def discover_models(client):
    resp = client.list()
    if hasattr(resp, "models"):
        return [m.model for m in resp.models]
    return [m["name"] for m in resp.get("models", [])]


def run_generate(client, model, prompt):
    t0 = time.time()
    first_token_time = None
    token_count = 0
    full_response = ""
    stream = client.generate(
        model=model, system=SYSTEM, prompt=prompt, stream=True, options=GEN_OPTIONS,
    )
    for chunk in stream:
        tok = chunk.response if hasattr(chunk, "response") else chunk.get("response", "")
        if tok:
            if first_token_time is None:
                first_token_time = time.time() - t0
            token_count += 1
            full_response += tok
    total = time.time() - t0
    return {
        "ttft_s":  round(first_token_time or 0, 2),
        "total_s": round(total, 2),
        "tok_s":   round(token_count / total, 1) if total > 0 else 0,
        "words":   len(full_response.split()),
    }


def run_chat(client, model, prompt):
    t0 = time.time()
    first_token_time = None
    token_count = 0
    full_response = ""
    stream = client.chat(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user",   "content": prompt},
        ],
        stream=True,
        options=GEN_OPTIONS,
    )
    for chunk in stream:
        if hasattr(chunk, "message"):
            tok = chunk.message.content or ""
        elif isinstance(chunk, dict):
            tok = chunk.get("message", {}).get("content", "")
        else:
            tok = ""
        if tok:
            if first_token_time is None:
                first_token_time = time.time() - t0
            token_count += 1
            full_response += tok
    total = time.time() - t0
    return {
        "ttft_s":  round(first_token_time or 0, 2),
        "total_s": round(total, 2),
        "tok_s":   round(token_count / total, 1) if total > 0 else 0,
        "words":   len(full_response.split()),
    }


def run_benchmark():
    client = ollama.Client(host=OLLAMA_URL)

    print(f"\n{BOLD}{'═'*70}{RESET}")
    print(f"{BOLD}  Ollama Model Benchmark  |  {OLLAMA_URL}{RESET}")

    models = discover_models(client)
    print(f"{BOLD}  Found {len(models)} models: {', '.join(models)}{RESET}")
    print(f"{BOLD}  Modes: generate (raw)  vs  instruct (chat template){RESET}")
    print(f"{BOLD}  Prompts: {len(PROMPTS)}  |  max_tokens: {GEN_OPTIONS['num_predict']}{RESET}")
    print(f"{BOLD}{'═'*70}{RESET}\n")

    results = {m: {"generate": [], "instruct": []} for m in models}
    total_runs = len(models) * 2 * len(PROMPTS)
    run_idx = 0

    for pidx, (label, prompt) in enumerate(PROMPTS, 1):
        print(f"{CYAN}{BOLD}[Prompt {pidx}/{len(PROMPTS)}] {label}{RESET}")
        print(f"  {DIM}{prompt[:90]}{'...' if len(prompt) > 90 else ''}{RESET}\n")

        for model in models:
            for mode, fn in [("generate", run_generate), ("instruct", run_chat)]:
                run_idx += 1
                print(f"  [{run_idx:2}/{total_runs}] {model:<22} [{mode:<8}] ...", end="", flush=True)
                try:
                    r = fn(client, model, prompt)
                    results[model][mode].append(r)
                    print(f"\r  [{run_idx:2}/{total_runs}] {model:<22} [{mode:<8}]  "
                          f"TTFT:{r['ttft_s']:4.1f}s  Total:{r['total_s']:5.1f}s  "
                          f"{r['tok_s']:4.0f}tok/s  {r['words']:4}w")
                except Exception as e:
                    results[model][mode].append({"ttft_s": 0, "total_s": 0, "tok_s": 0, "words": 0})
                    print(f"\r  [{run_idx:2}/{total_runs}] {model:<22} [{mode:<8}]  ERROR: {e}")
        print()

    # -- Compute averages --
    for m in models:
        for mode in ["generate", "instruct"]:
            rs = [r for r in results[m][mode] if r["total_s"] > 0]
            if rs:
                n = len(rs)
                results[m][mode + "_avg"] = {
                    "ttft_s":  round(sum(r["ttft_s"]  for r in rs) / n, 2),
                    "total_s": round(sum(r["total_s"] for r in rs) / n, 2),
                    "tok_s":   round(sum(r["tok_s"]   for r in rs) / n, 1),
                    "words":   round(sum(r["words"]   for r in rs) / n, 1),
                }
            else:
                results[m][mode + "_avg"] = {"ttft_s": 0, "total_s": 0, "tok_s": 0, "words": 0}

    # -- Mode comparison table --
    col_w = 14
    columns = []
    for m in models:
        short = m.split(":")[0][:10]
        columns += [f"{short}/gen", f"{short}/inst"]
    total_w = 26 + (col_w + 1) * len(columns)

    print(f"\n{BOLD}{'═'*total_w}{RESET}")
    print(f"{BOLD}  MODE COMPARISON: generate vs instruct  (averages over {len(PROMPTS)} prompts){RESET}")
    print(f"{BOLD}{'═'*total_w}{RESET}")
    hdr = f"  {'Metric':<22}" + "".join(f" {c:<{col_w}}" for c in columns)
    print(f"{YELLOW}{hdr}{RESET}")
    print("─" * total_w)

    for metric_label, metric_key, lower in [
        ("Avg TTFT (s)",  "ttft_s",  True),
        ("Avg Total (s)", "total_s", True),
        ("Avg tok/s",     "tok_s",   False),
        ("Avg words",     "words",   False),
    ]:
        vals = []
        for m in models:
            vals.append(results[m]["generate_avg"][metric_key])
            vals.append(results[m]["instruct_avg"][metric_key])
        colored = best_color(vals, lower)
        row = f"  {metric_label:<22}" + "".join(f" {c:<{col_w+9}}" for c in colored)
        print(row)

    # -- Final ranking --
    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  FINAL RANKING  (by Avg Total time, best mode per model){RESET}")
    print(f"{BOLD}{'═'*60}{RESET}")

    ranking = []
    for m in models:
        gen  = results[m]["generate_avg"]
        inst = results[m]["instruct_avg"]
        if inst["total_s"] > 0 and (gen["total_s"] == 0 or inst["total_s"] < gen["total_s"]):
            best_mode, best = "instruct", inst
        else:
            best_mode, best = "generate", gen
        ranking.append((m, best_mode, best))
    ranking.sort(key=lambda x: x[2]["total_s"])

    medals = ["🥇", "🥈", "🥉"]
    print(f"\n  {'':4} {'Model':<22} {'Mode':<10} {'Avg TTFT':>9} {'Avg Total':>10} {'tok/s':>7} {'words':>7}")
    print("  " + "─" * 66)
    for pos, (m, mode, avg) in enumerate(ranking, 1):
        medal = medals[pos - 1] if pos <= 3 else f"  {pos}."
        print(f"  {medal}  {m:<22} [{mode:<8}]  "
              f"{avg['ttft_s']:>8.1f}s  {avg['total_s']:>8.1f}s  "
              f"{avg['tok_s']:>7.1f}  {avg['words']:>7.0f}")

    fastest = ranking[0]
    most_words = max(ranking, key=lambda x: x[2]["words"])
    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  🏆 Fastest:    {fastest[0]}  [{fastest[1]}]  — {fastest[2]['total_s']:.1f}s avg{RESET}")
    print(f"{BOLD}  📝 Wordiest:   {most_words[0]}  [{most_words[1]}]  — {most_words[2]['words']:.0f} words avg{RESET}")

    # instruct vs generate improvement summary
    print(f"\n{BOLD}  instruct vs generate improvement:{RESET}")
    for m in models:
        g = results[m]["generate_avg"]["total_s"]
        i = results[m]["instruct_avg"]["total_s"]
        if g > 0 and i > 0:
            diff = round((g - i) / g * 100, 1)
            icon = "✅" if diff > 0 else "❌"
            direction = "faster" if diff > 0 else "slower"
            print(f"  {icon} {m:<22}  instruct is {abs(diff):.1f}% {direction} than generate")
    print(f"{BOLD}{'═'*60}{RESET}\n")

    # -- Save raw results --
    out = {m: {k: v for k, v in results[m].items()} for m in models}
    with open("/home/jartymyt/k8s-ai/bench_results.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"  Raw results saved → bench_results.json\n")


if __name__ == "__main__":
    run_benchmark()
