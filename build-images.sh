#!/bin/bash
# Build and push Docker images for the Spotify Playlist Recommendation System
# This script builds both the ML and Frontend containers

set -e  # Exit on error

# Configuration - UPDATE THESE VALUES
DOCKER_REGISTRY="docker.io"  # or "docker.io" for DockerHub
DOCKER_USERNAME="giovana2ma"  # Replace with your username
VERSION="0.1"  # Update this when you make changes

# Image names
ML_IMAGE="${DOCKER_REGISTRY}/${DOCKER_USERNAME}/playlists-ml"
FRONTEND_IMAGE="${DOCKER_REGISTRY}/${DOCKER_USERNAME}/playlists-frontend"

echo "======================================================================"
echo "Building Docker Images for Spotify Playlist Recommendation System"
echo "======================================================================"
echo "ML Image: ${ML_IMAGE}:${VERSION}"
echo "Frontend Image: ${FRONTEND_IMAGE}:${VERSION}"
echo "======================================================================"

# Build ML Container
echo ""
echo "Building ML Container..."
cd model
docker build -t "${ML_IMAGE}:${VERSION}" -t "${ML_IMAGE}:latest" .
cd ..
echo "✓ ML Container built successfully"

# Build Frontend Container
echo ""
echo "Building Frontend Container..."
cd api
docker build -t "${FRONTEND_IMAGE}:${VERSION}" -t "${FRONTEND_IMAGE}:latest" .
cd ..
echo "✓ Frontend Container built successfully"

echo ""
echo "======================================================================"
echo "Build Complete!"
echo "======================================================================"
echo "Images created:"
echo "  - ${ML_IMAGE}:${VERSION}"
echo "  - ${ML_IMAGE}:latest"
echo "  - ${FRONTEND_IMAGE}:${VERSION}"
echo "  - ${FRONTEND_IMAGE}:latest"
echo ""
echo "Next steps:"
echo "  1. Test the images locally (see test-containers.sh)"
echo "  2. Login to registry: docker login ${DOCKER_REGISTRY}"
echo "  3. Push images: ./push-images.sh"
echo "======================================================================"
