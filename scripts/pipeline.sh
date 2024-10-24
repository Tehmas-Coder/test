#!/bin/bash

# Exit if non-zero status
set -e

# Load environment variables based on the selected environment
if [ -f "/var/lib/jenkins/workspace/envs/.env.${ENVIRONMENT}.psychometric" ]; then
    export $(grep -v '^#' /var/lib/jenkins/workspace/envs/.env.${ENVIRONMENT}.psychometric | xargs)
    echo "Environment variables loaded from .env.${ENVIRONMENT}.psychometric"
else
    echo ".env.${ENVIRONMENT}.psychometric file not found!"
    exit 1
fi

# Move to the correct directory
cd "$CODE_DIRECTORY"

echo "Fixing file and directory permissions..."
sudo chown jenkins:jenkins "$ENV_FILE_PATH" "$SHELL_SCRIPT_PATH"
sudo chmod +x "$SHELL_SCRIPT_PATH"
sudo chmod 644 "$ENV_FILE_PATH"
echo "Permissions fixed for the environment file and shell script."

# Activate the virtual environment
source "$VENV_PATH/bin/activate"

# Update system packages
echo "Updating system packages..."
sudo apt update -y

# Install required packages from requirements.txt
echo "Installing dependencies from requirements.txt..."
pip install -r "$CODE_DIRECTORY/requirements.txt"

# Run database migrations
echo "Running database migrations..."
python manage.py migrate

# Start the Django application with Gunicorn
echo "Starting Django application with Gunicorn..."
gunicorn --chdir "$CODE_DIRECTORY" --bind 0.0.0.0:8000 "$CODE_DIRECTORY.wsgi:application" --daemon

# Restart NGINX
echo "Restarting NGINX..."
sudo systemctl restart nginx

echo "Django application started successfully!"

