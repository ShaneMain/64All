#!/bin/bash

set -e

function is_venv_active() {
    [ -n "$VIRTUAL_ENV" ]
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."
PYPROJECT_TOML_PATH="$PROJECT_ROOT/pyproject.toml"

if [ ! -f "$PYPROJECT_TOML_PATH" ]; then
    echo "Error: pyproject.toml file not found at $PYPROJECT_TOML_PATH."
    exit 1
fi

cd "$PROJECT_ROOT"

export PATH="$HOME/.local/bin:$PATH"

if ! command -v poetry &> /dev/null; then
    echo "Error: Poetry is not found in PATH. Install it or check your environment setup."
    exit 1
fi

poetry install

poetry run python3 -m pip install toml pyqt6 gitpython pyyaml

echo "Dependencies from pyproject.toml:"
poetry run python3 << EOF
import toml

def get_dependencies(pyproject_file):
    with open(pyproject_file, 'r') as f:
        pyproject_data = toml.load(f)

    dependencies = pyproject_data.get('tool', {}).get('poetry', {}).get('dependencies', {})
    return dependencies

dependencies = get_dependencies('$PYPROJECT_TOML_PATH')
for package, version in dependencies.items():
    print(f"{package} == {version}")
EOF

PYTHON_PREFIX=$(pyenv prefix 3.11.5)
PYTHON_VERSION="3.11.5"
echo "Python Prefix: $PYTHON_PREFIX"

LIB_PYTHON_PATH="$PYTHON_PREFIX/lib/libpython3.11.so.1.0"
echo "Library Path: $LIB_PYTHON_PATH"

if [ ! -f "$LIB_PYTHON_PATH" ]; then
    echo "Error: libpython3.11.so.1.0 was not found in pyenv directories."
    exit 1
fi

LIB_TYPE=$(file "$LIB_PYTHON_PATH")
if ! echo "$LIB_TYPE" | grep -q "64-bit"; then
    echo "Error: The library at $LIB_PYTHON_PATH is not a 64-bit version."
    exit 1
fi

echo "Library found at $LIB_PYTHON_PATH"

rm -rf build dist 64All.spec
mkdir -p build/64All/lib

# Copy the Python library
cp "$LIB_PYTHON_PATH" build/64All/lib

# Define the build directory
BUILD_DIR="build/64All/lib"
# Get the site-packages directory for hidden imports
SITE_PACKAGES_DIR=$(poetry run python3 -c "import site; print(site.getsitepackages()[0])")

export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

echo "Creating spec file..."
cat << 'EOF' > 64All.spec
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Collect hidden imports
hiddenimports = collect_submodules('src.main')

a = Analysis(
    ['src/main.py'],  # Entry point of your application
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],  # Specify your custom hooks directory if any
    noarchive=True,  # Enable noarchive to improve loading time
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    exclude_binaries=True,  # Exclude binaries to reduce size
    name='64AllExecutable',  # Change the name of the executable
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=True,
    onefile=True
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=True,
    name='64All',
)
EOF

echo "Creating the executable..."
poetry run pyinstaller 64All.spec

echo "Directory structure after build:"
ls -R dist

# Check the dist directory for the expected output
DIST_DIR="dist"
if [ ! -d "$DIST_DIR" ]; then
    echo "Error: Directory $DIST_DIR was not found."
    exit 1
fi

EXECUTABLE_FILE="$DIST_DIR/64AllExecutable"
if [ ! -f "$EXECUTABLE_FILE" ]; then
    echo "Error: $EXECUTABLE_FILE was not found."
    exit 1
fi

echo "Executable created successfully at $EXECUTABLE_FILE."