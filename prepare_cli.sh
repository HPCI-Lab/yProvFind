#!/bin/bash

# Get the directory of this script, resolving any symlinks
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

# Move to script directory
pushd "$SCRIPT_DIR" > /dev/null || exit 1

# Check if 'uv' is installed
echo "Checking for uv..."
if ! command -v uv &> /dev/null; then
    echo "uv not found. Installing uv..."
    pip install uv
else
    echo "uv is already installed."
fi

# Recreate venv only if needed
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  uv venv .venv
else
  echo "Using existing virtual environment..."
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Navigate to CLI directory and install in editable mode
echo "Installing CLI in editable mode..."
if [ -d "src/cli" ]; then
  cd src/cli || exit 1
  uv pip install -e .
  cd ../.. || exit 1
else
  echo "Error: src/cli directory not found!"
  popd > /dev/null || true
  exit 1
fi

# Export the PYTHONPATH (pointing to the CLI directory)
export PYTHONPATH="${PYTHONPATH}:${SCRIPT_DIR}/src/cli"

# Return to the original directory
popd > /dev/null || true

echo ""
echo "========================================"
echo "CLI installed successfully!"
echo "========================================"
echo ""
echo "To use the CLI:"
echo "1. Activate the virtual environment: source .venv/bin/activate"
echo "2. Run your CLI command"
echo ""
echo "PYTHONPATH has been set to: ${SCRIPT_DIR}/src/cli"