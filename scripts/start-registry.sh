#!/bin/bash

# Start local Docker registry for testing custom containers
set -e

REGISTRY_CONTAINER="k8sgpt-registry"
REGISTRY_PORT="5000"

echo "🐳 Starting local Docker registry on port $REGISTRY_PORT..."

# Check if registry is already running
if docker ps | grep -q "$REGISTRY_CONTAINER"; then
    echo "✅ Registry is already running"
    exit 0
fi

# Start registry
docker run -d \
    --name "$REGISTRY_CONTAINER" \
    -p "$REGISTRY_PORT:5000" \
    --restart always \
    registry:2

if [ $? -eq 0 ]; then
    echo "✅ Local Docker registry started successfully"
    echo "📍 Registry URL: localhost:$REGISTRY_PORT"
    echo ""
    echo "To build and push containers:"
    echo "  ./build.sh"
    echo ""
    echo "To stop registry:"
    echo "  docker stop $REGISTRY_CONTAINER && docker rm $REGISTRY_CONTAINER"
else
    echo "❌ Failed to start registry"
    exit 1
fi