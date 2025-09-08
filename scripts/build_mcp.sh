#!/usr/bin/env zsh

set -euo pipefail

# Simple log helper, unified info and error output format
info() { echo "[INFO] $*"; }
err()  { echo "[ERROR] $*" >&2; }

# Get script directory and project root directory
SCRIPT_DIR="$(cd "$(dirname "$0")" >/dev/null 2>&1 && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." >/dev/null 2>&1 && pwd)"

info "=== Build process started ==="

# Default supported platforms
PLATFORMS="linux/amd64,linux/arm64"
# PLATFORMS="linux/amd64"
# Default image name
IMAGE_NAME="sacahan/graphiti-mcp"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    err "Docker is not installed. Please install Docker first."
    err "=== Build failed ==="
    exit 1
fi

BUILDER_NAME="multiarch-builder"
if ! docker buildx inspect "$BUILDER_NAME" &> /dev/null; then
    info "Creating buildx builder: $BUILDER_NAME"
    docker buildx create --name "$BUILDER_NAME" --driver docker-container --use
else
    info "Using existing buildx builder: $BUILDER_NAME"
    docker buildx use "$BUILDER_NAME"
fi

docker buildx inspect --bootstrap

info "Registering QEMU multiarch binfmt support (Docker must allow --privileged) ..."
docker run --rm --privileged tonistiigi/binfmt:latest --install all || \
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes || true

DOCKERFILE_PATH="$PROJECT_ROOT/mcp_server/Dockerfile.falkordb"
IMAGE_TAG="${IMAGE_NAME}:latest"

info "Build and push multi-platform image: image=$IMAGE_TAG, dockerfile=$DOCKERFILE_PATH"
# buildx --push only pushes, does not keep local image
docker buildx build --platform "$PLATFORMS" --push -t "$IMAGE_TAG" -f "$DOCKERFILE_PATH" "$PROJECT_ROOT"

info "=== Build completed ==="
