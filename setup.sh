#!/bin/bash
# UHB — Universal Harness Benchmark — One-Command Setup
# curl -fsSL https://.../setup.sh | bash
# or: bash setup.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════╗"
echo "║   🧬 UHB — Universal Harness Benchmark       ║"
echo "║   AI Developer Research Platform             ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python
PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" &>/dev/null; then
    echo -e "${RED}Python 3 not found. Install Python 3.10+ first.${NC}"
    exit 1
fi

PYVER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "Python: ${GREEN}$PYVER${NC}"

# Install core dependencies
echo -e "\n${CYAN}[1/3] Installing core dependencies...${NC}"
"$PYTHON" -m pip install -q anthropic openai pyyaml pydantic diskcache 2>/dev/null || true

# Install all UHB packages in dev mode
echo -e "${CYAN}[2/3] Installing UHB packages...${NC}"
for pkg_dir in uhb-core uhb-benchmark uhb-environment uhb-personality uhb-memory uhb-tools uhb-evolution uhb-compiler uhb-systems uhb-community uhb-dashboard; do
    if [ -d "$pkg_dir" ]; then
        "$PYTHON" -m pip install -q -e "$pkg_dir" 2>/dev/null && \
            echo -e "  ${GREEN}✓${NC} $pkg_dir" || \
            echo -e "  ${RED}✗${NC} $pkg_dir (non-critical)"
    fi
done

# Make CLI accessible
echo -e "${CYAN}[3/3] Configuring CLI...${NC}"
chmod +x "$SCRIPT_DIR/uhb"
UHBBIN="$HOME/.local/bin"
mkdir -p "$UHBBIN"
ln -sf "$SCRIPT_DIR/uhb" "$UHBBIN/uhb" 2>/dev/null || true
echo -e "  ${GREEN}✓${NC} uhb → $UHBBIN/uhb"

# Verify
echo -e "\n${GREEN}Setup complete!${NC}"
echo ""
echo -e "Run a quick test:"
echo -e "  ${CYAN}uhb benchmark mock/medium${NC}"
echo ""
echo -e "Or see all commands:"
echo -e "  ${CYAN}uhb --help${NC}"

# If UHBBIN isn't in PATH, suggest adding it
if ! echo "$PATH" | grep -q "$UHBBIN"; then
    echo ""
    echo -e "${RED}Note:${NC} Add $UHBBIN to your PATH:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo "  (add this to your ~/.bashrc or ~/.zshrc)"
fi
