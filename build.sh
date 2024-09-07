#!/bin/bash

set -e

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

# Activate the virtual environment
pyenv activate venv-3.11.5

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
echo "Python Prefix: $PYTHON_PREFIX"

# Directly assign the library path
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

# Set LD_LIBRARY_PATH for the current session
export LD_LIBRARY_PATH=$(dirname "$LIB_PYTHON_PATH")
echo "LD_LIBRARY_PATH set to $LD_LIBRARY_PATH"

# Clean previous builds
rm -rf build dist 64All.spec

# Create a lib directory within the build structure
mkdir -p build/64All/_internal

# Copy the library to the build _internal directory
cp "$LIB_PYTHON_PATH" build/64All/_internal

# Generate the spec file for PyInstaller
echo "Creating spec file..."
cat << EOF > 64All.spec
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[('build/64All/_internal/libpython3.11.so.1.0', './_internal')],
    datas=[],
    hiddenimports=['ttkthemes', 'theme_setter', 'gitlogic'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='64All',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='64All'
)
EOF

# Create the executable
echo "Creating the executable..."
poetry run pyinstaller 64All.spec

# Ensure the shared library is included properly in the dist directory
DIST_DIR="dist/64All"
LIB_DIR="$DIST_DIR/_internal"
mkdir -p "$LIB_DIR"
cp "$LIB_PYTHON_PATH" "$LIB_DIR"

echo "Executable created successfully. Library copied to $LIB_DIR."