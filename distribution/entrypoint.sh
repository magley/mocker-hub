#!/bin/sh

REGISTRY_STORAGE_PATH="/var/lib/registry/docker/registry/v2/repositories"

if [ "$RUN_REGISTRY_GC" = "true" ]; then
    if [ -d "$REGISTRY_STORAGE_PATH" ]; then
        echo "Running Distribution garbage collection..."
        registry garbage-collect /etc/docker/registry/config.yml --delete-untagged
    else
        echo "Skipping garbage collection: No images have ever been pushed by any user."
    fi
else
    echo "Skipping garbage collection: RUN_REGISTRY_GC is not true."
fi

echo "Starting Distribution..."
exec registry serve /etc/docker/registry/config.yml