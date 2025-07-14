#!/bin/bash
# Backend Docker entrypoint script
# Handles Docker socket permissions and starts the Flask app

set -e

# Function to check if we're running in Docker
is_docker() {
    [ -f /.dockerenv ] || grep -q 'docker\|lxc' /proc/1/cgroup 2>/dev/null
}

# If Docker socket is mounted and we're in Docker, ensure proper permissions
if [ -S /var/run/docker.sock ] && is_docker; then
    echo "🔧 Docker socket detected, configuring permissions..."
    
    # Get the GID of the docker socket
    DOCKER_GID=$(stat -c '%g' /var/run/docker.sock)
    
    # Create docker group with the same GID if it doesn't exist
    if ! getent group docker >/dev/null 2>&1; then
        groupadd -g ${DOCKER_GID} docker
        echo "✅ Created docker group with GID ${DOCKER_GID}"
    fi
    
    # Add the current user to the docker group
    if [ -n "$USER" ] && [ "$USER" != "root" ]; then
        usermod -aG docker $USER
        echo "✅ Added user $USER to docker group"
    fi
    
    # Alternative: If we can't modify groups, try to make socket accessible
    # This is less secure but works in more environments
    if ! groups | grep -q docker; then
        echo "⚠️  Could not add user to docker group, trying alternative approach..."
        # This requires the container to run with sufficient privileges
        chmod 666 /var/run/docker.sock 2>/dev/null || \
            echo "❌ Could not modify Docker socket permissions. Service restart functionality may not work."
    fi
fi

# Execute the main command
echo "🚀 Starting Flask backend..."
exec "$@"