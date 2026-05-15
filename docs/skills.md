# AI Skills Configuration

## Overview

AI Skills are the **system prompts** injected into the LLM for each feature. They define the AI's persona, tone, output format, and expertise area.

There are two skills:

| Skill | Used by | Env var |
|---|---|---|
| `skills.insights` | AI Insights tab | `AI_SKILL_INSIGHTS` |
| `skills.chat` | AI Chat tab | `AI_SKILL_CHAT` |

## Editing Skills

Skills are stored in `values.yaml`. Edit them directly — **no Docker image rebuild required**. Only a `helm upgrade` is needed.

```yaml
# values.yaml
skills:
  insights: |
    You are an expert Kubernetes L2/L3 support engineer at a manufacturing company.
    Your role is to analyze Kubernetes cluster data and provide clear, actionable insights.
    ...

  chat: |
    You are an expert Kubernetes L2/L3 support engineer assistant.
    You have access to LIVE CLUSTER DATA provided at the start of each conversation.
    ALWAYS answer using EXACT numbers from the data. Never say "I don't know the exact number".
    ...
```

After editing:

```bash
./scripts/build-deploy.sh --values-only
# or manually:
helm upgrade ai-local ./helm \
  --namespace ai-local \
  -f helm/values.yaml \
  -f helm/values-<cluster>.yaml
```

## How Skills Are Injected

```
values.yaml
  skills.insights  ──────────┐
  skills.chat  ──────────────┤
                             ▼
          templates/webui/webui-skills-configmap.yaml
          (ConfigMap: ai-local-k8sgpt-ai-analyzer-skills)
                             │
                             ▼ envFrom.configMapRef
          webui pod
          AI_SKILL_INSIGHTS=<skills.insights value>
          AI_SKILL_CHAT=<skills.chat value>
                             │
                             ▼
          app.py (at startup)
          AI_SKILL_INSIGHTS = os.environ.get('AI_SKILL_INSIGHTS', _DEFAULT_INSIGHTS_SKILL)
          AI_SKILL_CHAT = os.environ.get('AI_SKILL_CHAT', _DEFAULT_CHAT_SKILL)
```

## Fallback Defaults

If the env vars are not set (e.g., running locally without Helm), `app.py` uses hardcoded defaults (`_DEFAULT_INSIGHTS_SKILL`, `_DEFAULT_CHAT_SKILL`). These are defined at the top of `app.py`.

To override locally (development):

```bash
export AI_SKILL_INSIGHTS="You are a helpful Kubernetes assistant..."
export AI_SKILL_CHAT="You are a helpful Kubernetes chat assistant..."
streamlit run app.py
```

## YAML Formatting Rules

Skills are multiline strings using the YAML `|` (literal block scalar) operator:

```yaml
skills:
  insights: |
    First line of the prompt.
    Second line.
    ...
```

Rules:
- Always use `|` (not `>` — which folds newlines)
- Indent the content consistently (2 or 4 spaces)
- Do NOT add extra blank lines at the start of the block
- The string is injected verbatim as `AI_SKILL_INSIGHTS` env var

## Verifying Applied Skills

After `helm upgrade`, verify the ConfigMap was updated:

```bash
kubectl get configmap -n ai-local ai-local-k8sgpt-ai-analyzer-skills -o yaml
```

Verify the pod picked up the new env vars (pod must restart after ConfigMap update):

```bash
kubectl rollout restart deployment -n ai-local ai-local-ai-webui
kubectl exec -n ai-local deploy/ai-local-ai-webui -- env | grep AI_SKILL
```

## Skill Writing Guidelines

### For `skills.insights` (AI Insights tab)

The model will receive structured cluster data (JSON-like) and must produce a **formatted report**.

Recommended elements:
- Define the output structure (numbered sections, headers)
- Specify language (default: English)
- Instruct to be factual and reference exact pod/node names
- Tell the model to include `kubectl` commands for remediation
- Limit verbosity — avoid generic advice

### For `skills.chat` (AI Chat tab)

The model receives the cluster context block + user question in conversation mode.

Recommended elements:
- Instruct to use EXACT numbers from the context
- Tell it the context was fetched live and is current
- Define what to do when asked about something not in context
- Specify response format (short answers are better in chat)
- Language instruction
