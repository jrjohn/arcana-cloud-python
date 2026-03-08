#!/bin/bash
# K8s smoke test using kind for arcana-cloud-python
# Usage: ./scripts/kind-smoke-test.sh <image:tag> <protocol> [timeout_seconds]
#
# Examples:
#   ./scripts/kind-smoke-test.sh localhost:5000/arcana/python-app:build-42 grpc 480

set -euo pipefail

IMAGE="${1:-localhost:5000/arcana/python-app:latest}"
PROTOCOL="${2:-grpc}"
TIMEOUT="${3:-480}"

# Configuration
CLUSTER_NAME="arcana-ci-python-${PROTOCOL}"
IMAGE_ALIAS="arcana-cloud-python:ci"
NS="arcana-ci-kind-python"
NODE_PORT="30095"
MANIFEST="deployment/kubernetes/ci/kind-ci-grpc.yaml"
EXPECTED_PODS=3

echo "=== Kind K8s Smoke Test: ${PROTOCOL} ==="
echo "    Cluster:  ${CLUSTER_NAME}"
echo "    Image:    ${IMAGE} → ${IMAGE_ALIAS}"
echo "    Manifest: ${MANIFEST}"
echo "    Timeout:  ${TIMEOUT}s"

# ---------------------------------------------------------------------------
# Cleanup helper
# ---------------------------------------------------------------------------
cleanup() {
  echo "[cleanup] Deleting kind cluster ${CLUSTER_NAME} ..."
  kind delete cluster --name "${CLUSTER_NAME}" 2>/dev/null || true
}
trap cleanup EXIT

# ---------------------------------------------------------------------------
# Create kind cluster (delete any stale cluster with the same name first)
# ---------------------------------------------------------------------------
echo "[kind] Checking for existing cluster ${CLUSTER_NAME} ..."
if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
  echo "[kind] Deleting stale cluster ${CLUSTER_NAME} ..."
  kind delete cluster --name "${CLUSTER_NAME}" 2>/dev/null || true
fi

echo "[kind] Creating cluster ${CLUSTER_NAME} ..."
kind create cluster --name "${CLUSTER_NAME}" --wait 60s

# ---------------------------------------------------------------------------
# Load image into kind
# ---------------------------------------------------------------------------
echo "[kind] Loading image ${IMAGE} as ${IMAGE_ALIAS} ..."

# Pull image from local registry if needed
if ! docker image inspect "${IMAGE}" > /dev/null 2>&1; then
  echo "[kind] Pulling ${IMAGE} from registry ..."
  docker pull "${IMAGE}"
fi

# Tag for kind (imagePullPolicy: Never)
docker tag "${IMAGE}" "${IMAGE_ALIAS}"
kind load docker-image "${IMAGE_ALIAS}" --name "${CLUSTER_NAME}"

# ---------------------------------------------------------------------------
# Apply manifest
# ---------------------------------------------------------------------------
echo "[k8s] Applying manifest ${MANIFEST} ..."
# Wait a moment for the API server to be fully reachable
sleep 5
kubectl apply -f "${MANIFEST}" --validate=false

# ---------------------------------------------------------------------------
# Wait for pods to be ready
# ---------------------------------------------------------------------------
wait_pod() {
  local label="$1"
  local elapsed=0
  local interval=10

  echo "[k8s] Waiting for pod (app=${label}) to be ready ..."
  while true; do
    local ready
    ready=$(kubectl get pods -n "${NS}" -l "app=${label}" \
      -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "")

    if [[ "${ready}" == *"True"* ]]; then
      echo "[k8s] Pod ${label} is ready after ${elapsed}s"
      return 0
    fi

    if [[ ${elapsed} -ge ${TIMEOUT} ]]; then
      echo "[k8s] TIMEOUT waiting for ${label} pods after ${TIMEOUT}s"
      kubectl get pods -n "${NS}" 2>/dev/null || true
      kubectl describe pods -n "${NS}" -l "app=${label}" 2>/dev/null | tail -40 || true
      return 1
    fi

    sleep ${interval}
    elapsed=$((elapsed + interval))
    echo "[k8s] ...${elapsed}s elapsed, waiting for ${label}"
  done
}

# Wait for all layers in order (dependency chain)
wait_pod "arcana-ci-repository"
wait_pod "arcana-ci-service"
wait_pod "arcana-ci-controller"

# Verify expected pod count
RUNNING_PODS=$(kubectl get pods -n "${NS}" \
  -l "app in (arcana-ci-repository,arcana-ci-service,arcana-ci-controller)" \
  --field-selector=status.phase=Running \
  --no-headers 2>/dev/null | wc -l | tr -d ' ')
echo "[k8s] Running app pods: ${RUNNING_PODS} / ${EXPECTED_PODS} expected"

# ---------------------------------------------------------------------------
# Get NodePort address
# ---------------------------------------------------------------------------
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null || echo "localhost")
BASE_URL="http://${NODE_IP}:${NODE_PORT}"

echo "[test] Smoke testing ${BASE_URL} ..."

# ---------------------------------------------------------------------------
# Run integration smoke test
# ---------------------------------------------------------------------------
bash scripts/integration-smoke-test.sh "${BASE_URL}" "k8s-grpc" 120

echo ""
echo "=== ✅ Kind K8s smoke test PASSED [${PROTOCOL}] ==="
