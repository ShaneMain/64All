#!/bin/bash

set -e

# Function to check if a virtual environment is active
function is_venv_active() {
    if [ -z "$VIRTUAL_ENV" ]; then
        return 1
    else
        return 0
    fi
}

# Add pyenv to PATH
export PATH="$HOME/.pyenv/bin:$PATH"

# Initialize pyenv
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# Ensure the virtual environment exists
if ! pyenv virtualenvs | grep -q "venv-3.11.5"; then
    pyenv virtualenv 3.11.5 venv-3.11.5
fi

# Activate the virtual environment if not already active
if ! is_venv_active; then
    pyenv activate venv-3.11.5
fi

# Check for correct working directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT_DIR" # Navigate to the root directory containing pyproject.toml

# Include Poetry installation path in the PATH
export PATH="$HOME/.local/bin:$PATH"

# Verify that Poetry is available
if ! command -v poetry &> /dev/null; then
    echo "Error: Poetry is not found in PATH. Install it or check your environment setup."
    exit 1
fi

# Ensure the pyproject.toml file is present
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml file not found in the current directory."
    exit 1
fi

# Use Poetry to install dependencies
poetry install

# Get the prefix directory
PYTHON_PREFIX=$(pyenv prefix 3.11.5)
PYTHON_VERSION="3.11.5"
echo "Python Prefix: $PYTHON_PREFIX"

# Define the library path
LIB_PYTHON_PATH="$PYTHON_PREFIX/lib/libpython3.11.so.1.0"
echo "Library Path: $LIB_PYTHON_PATH"

# Handle error if the library is not found
if [ ! -f "$LIB_PYTHON_PATH" ]; then
    echo "Error: libpython3.11.so.1.0 was not found in pyenv directories."
    exit 1
fi

# Verify the library is 64-bit
LIB_TYPE=$(file "$LIB_PYTHON_PATH")
if ! echo "$LIB_TYPE" | grep -q "64-bit"; then
    echo "Error: The library at $LIB_PYTHON_PATH is not a 64-bit version."
    exit 1
fi

echo "Library found at $LIB_PYTHON_PATH"

# Clean previous builds
rm -rf build dist 64All.spec

# Create a lib directory within the build structure
mkdir -p build/64All/lib

# Copy the library to the build lib directory
cp "$LIB_PYTHON_PATH" build/64All/lib

# Generate the spec file for PyInstaller
echo "Creating spec file..."
cat << EOF > 64All.spec
# Refined Spec file to manually include python encodings directory if needed
# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# Collect all hidden imports from encodings
hiddenimports = collect_submodules('encodings')

# Manually specify data files
encodings_path = os.path.join(sys.base_prefix, 'lib/python3.11/encodings')
datas = collect_data_files('encodings', include_py_files=True) + [
    (encodings_path, 'encodings')
]

a = Analysis(
    ['src/main.py'],  # Ensure 'main.py' path is updated
    pathex=['src'],  # Add 'src' to the path
    binaries=[
        ('build/64All/lib/libpython3.11.so.1.0', 'lib/libpython3.11.so.1.0')
    ],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=True
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    exclude_binaries=False,
    name='64All',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    onefile=True
)
EOF

# Create the executable
echo "Creating the executable..."
poetry run pyinstaller 64All.spec

# Print directory structure for debugging purposes
echo "Directory structure after build:"
ls -R

# Verify that the shared library is included properly
EXECUTABLE_FILE="dist/64All"
if [ ! -f "$EXECUTABLE_FILE" ]; then
    echo "Error: $EXECUTABLE_FILE was not found."
    exit 1
fi

echo "Executable created successfully at $EXECUTABLE_FILE."