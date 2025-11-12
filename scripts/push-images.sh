#!/bin/bash
# Push Docker images to the registry

set -e  # Exit on error

# Configuration - UPDATE THESE VALUES (must match build-images.sh)
DOCKER_REGISTRY="docker.io"  # or "docker.io" for DockerHub
DOCKER_USERNAME="giovana2ma"  # Replace with your username
VERSION="0.1"  # Update this when you make changes

# Image names
ML_IMAGE="${DOCKER_REGISTRY}/${DOCKER_USERNAME}/playlists-ml"
FRONTEND_IMAGE="${DOCKER_REGISTRY}/${DOCKER_USERNAME}/playlists-frontend"

echo "======================================================================"
echo "Pushing Docker Images to ${DOCKER_REGISTRY}"
echo "======================================================================"

# Check if logged in
echo "Checking authentication..."
if ! docker info 2>/dev/null | grep -q "Username"; then
    echo "Not logged in to Docker registry. Attempting login..."
    docker login "${DOCKER_REGISTRY}"
fi

# Push ML Container
echo ""
echo "Pushing ML Container..."
docker push "${ML_IMAGE}:${VERSION}"
docker push "${ML_IMAGE}:latest"
echo "✓ ML Container pushed successfully"

# Push Frontend Container
echo ""
echo "Pushing Frontend Container..."
docker push "${FRONTEND_IMAGE}:${VERSION}"
docker push "${FRONTEND_IMAGE}:latest"
echo "✓ Frontend Container pushed successfully"

echo ""
echo "======================================================================"
echo "Push Complete!"
echo "======================================================================"
echo "Images available at:"
echo "  - ${ML_IMAGE}:${VERSION}"
echo "  - ${FRONTEND_IMAGE}:${VERSION}"
echo ""
echo "Your images are now publicly accessible and ready for Kubernetes/ArgoCD"
echo "======================================================================"
