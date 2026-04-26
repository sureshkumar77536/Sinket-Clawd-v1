#!/bin/bash

echo -e "\033[1;36mStarting Sinket Clawd Installation...\033[0m"

# Update and install dependencies
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip git
fi

# Setup Directory
REPO_DIR="$HOME/.sinket_clawd"

if [ -d "$REPO_DIR" ]; then
    echo -e "\033[1;36mUpdating existing repository...\033[0m"
    cd "$REPO_DIR" && git pull origin main
else
    echo -e "\033[1;36mCloning repository...\033[0m"
    git clone https://github.com/sureshkumar77536/Sinket-Clawd-v1.git "$REPO_DIR"
fi

# Install Python requirements
echo -e "\033[1;36mInstalling Python requirements...\033[0m"
pip3 install -r "$REPO_DIR/requirements.txt" --break-system-packages || pip3 install -r "$REPO_DIR/requirements.txt"

# Make executable and setup global command
chmod +x "$REPO_DIR/sinkwd.py"
sudo ln -sf "$REPO_DIR/sinkwd.py" /usr/local/bin/sinkwd

echo -e "\033[1;32m✅ Installation Complete! Type 'sinkwd' anywhere in the terminal to start.\033[0m"
