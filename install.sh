#!/bin/bash

CYAN='\033[1;36m'
GREEN='\033[1;32m'
RED='\033[1;31m'
YELLOW='\033[1;33m'
RESET='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════╗${RESET}"
echo -e "${CYAN}║   SINKET CLAWD v2 — Zen Edition      ║${RESET}"
echo -e "${CYAN}╚══════════════════════════════════════╝${RESET}"
echo ""

# ─── Python 3.9+ Auto Check & Auto Install ───
PYTHON_CMD=""

check_python() {
    for cmd in python3.11 python3.10 python3.9 python3; do
        if command -v "$cmd" &> /dev/null; then
            ver=$($cmd --version 2>&1 | awk '{print $2}')
            major=$(echo "$ver" | cut -d. -f1)
            minor=$(echo "$ver" | cut -d. -f2)
            if [ "$major" -gt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -ge 9 ]; }; then
                PYTHON_CMD="$cmd"
                echo -e "${GREEN}✅ Python $ver found ($cmd)${RESET}"
                return 0
            fi
        fi
    done
    return 1
}

install_python() {
    echo -e "${YELLOW}⚠️  Python 3.9+ not found. Auto-installing...${RESET}"
    if command -v apt-get &> /dev/null; then
        sudo apt-get update -qq
        sudo apt-get install -y -qq software-properties-common
        sudo add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null || true
        sudo apt-get update -qq
        for py in python3.11 python3.10 python3.9; do
            if sudo apt-get install -y -qq "$py" "$py-pip" 2>/dev/null; then
                PYTHON_CMD="$py"
                echo -e "${GREEN}✅ Installed $py successfully${RESET}"
                return 0
            fi
        done
    elif command -v yum &> /dev/null; then
        sudo yum install -y python39 python39-pip 2>/dev/null && PYTHON_CMD="python3.9" && return 0
    elif command -v pacman &> /dev/null; then
        sudo pacman -Sy --noconfirm python 2>/dev/null && PYTHON_CMD="python3" && return 0
    fi
    echo -e "${RED}❌ Failed to auto-install Python 3.9+. Please install manually.${RESET}"
    exit 1
}

if ! check_python; then
    install_python
    if ! check_python; then
        echo -e "${RED}❌ Python 3.9+ still not available after install attempt.${RESET}"
        exit 1
    fi
fi

# ─── Install Git if missing ───
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}📦 Installing git...${RESET}"
    sudo apt-get install -y -qq git 2>/dev/null || sudo yum install -y git 2>/dev/null || true
fi

# ─── Clone/Update Repo ───
REPO_DIR="$HOME/.sinket_clawd"

if [ -d "$REPO_DIR" ]; then
    echo -e "${CYAN}🔄 Updating existing repository...${RESET}"
    cd "$REPO_DIR" && git pull origin main --quiet
else
    echo -e "${CYAN}📥 Cloning repository...${RESET}"
    git clone --depth 1 https://github.com/sureshkumar77536/Sinket-Clawd-v1.git "$REPO_DIR"
fi

# ─── Install Python Dependencies ───
echo -e "${CYAN}📦 Installing Python packages...${RESET}"
$PYTHON_CMD -m pip install --upgrade pip --quiet 2>/dev/null || true
$PYTHON_CMD -m pip install -r "$REPO_DIR/requirements.txt" --break-system-packages --quiet 2>/dev/null || \
$PYTHON_CMD -m pip install -r "$REPO_DIR/requirements.txt" --quiet 2>/dev/null || \
$PYTHON_CMD -m pip install -r "$REPO_DIR/requirements.txt" --user --quiet

# ─── Setup Global Command ───
chmod +x "$REPO_DIR/sinkwd.py"
sudo ln -sf "$REPO_DIR/sinkwd.py" /usr/local/bin/sinkwd

echo ""
echo -e "${GREEN}✅ Installation Complete!${RESET}"
echo -e "${CYAN}   Type 'sinkwd' anywhere to start.${RESET}"
