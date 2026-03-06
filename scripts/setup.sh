#!/usr/bin/env bash
set -euo pipefail

echo "Setting up gt-python development environment..."

# Check for uv
if ! command -v uv &> /dev/null; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  echo "uv installed. You may need to restart your shell or source your profile."
fi

# Install all workspace packages
echo "Installing workspace packages..."
uv sync --all-packages

# Check for cargo (needed for sampo)
if ! command -v cargo &> /dev/null; then
  echo "Installing Rust toolchain (needed for sampo)..."
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
  source "$HOME/.cargo/env"
fi

# Install sampo
if ! command -v sampo &> /dev/null; then
  echo "Installing sampo..."
  cargo install sampo
fi

echo "Setup complete!"
echo "  uv:    $(uv --version)"
echo "  sampo: $(sampo --version)"
