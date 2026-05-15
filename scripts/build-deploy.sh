#!/bin/bash
# Build, push and deploy the webui image.
# Usage:
#   ./scripts/build-deploy.sh <tag>
#   ./scripts/build-deploy.sh v2026-03-17-17
set -e

REGISTRY="${REGISTRY:-central-system-repo.app.corp:10443/9tech/ai/webui}"
TAG="${1:?Usage: $0 <tag>}"
IMAGE="${REGISTRY}:${TAG}"
KUBECONFIG_PATH="${KUBECONFIG:-/home/jartymyt/kubeconfig/eudrpkbe0001.kubeconfig}"
HELM_RELEASE="${HELM_RELEASE:-ai-local}"
NAMESPACE="${NAMESPACE:-ai-local}"
HELM_CHART_DIR="${HELM_CHART_DIR:-$(dirname "$0")/../helm}"
LOCAL_VALUES="${LOCAL_VALUES:-${HELM_CHART_DIR}/values-eudrpkbe0001.yaml}"

echo "▶ Building  ${IMAGE}"
docker build -t "${IMAGE}" .

echo "▶ Pushing   ${IMAGE}"
docker push "${IMAGE}"

echo "▶ Deploying via Helm (release=${HELM_RELEASE}, ns=${NAMESPACE})"
KUBECONFIG="${KUBECONFIG_PATH}" helm upgrade "${HELM_RELEASE}" "${HELM_CHART_DIR}" \
    --namespace "${NAMESPACE}" \
    -f "${HELM_CHART_DIR}/values.yaml" \
    -f "${LOCAL_VALUES}" \
    --set webui.image.tag="${TAG}"

echo "✅ Done — ${IMAGE}"
