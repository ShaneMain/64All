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

poetry run python3 -m pip install toml pyqt6 modulegraph gitpython pyyaml

PYTHON_PREFIX=$(pyenv prefix 3.11.5)
LIB_PYTHON_PATH="$PYTHON_PREFIX/lib/libpython3.11.so.1.0"

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

# Define the build directory
BUILD_DIR="build/64All/lib"
mkdir -p $BUILD_DIR

cp "$LIB_PYTHON_PATH" "$BUILD_DIR"

export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

echo "Creating spec file..."
cat << 'EOF' > 64All.spec
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import PyQt6
import os
import modulegraph.modulegraph
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

def find_all_imports(entry_point):
    mg = modulegraph.modulegraph.ModuleGraph()
    mg.run_script(entry_point)
    return mg

# Entry point of your application
entry_point = 'src/main.py'
mg = find_all_imports(entry_point)

# Collect the necessary imports from `src.main`
my_package_hiddenimports = [
    node.identifier
    for node in mg.flatten()
    if node.identifier.startswith('src.main') and not node.identifier.endswith('__init__')
]

block_cipher = None

# Define the necessary paths for binaries and data files
binaries = []
datas = []

# Collect data files from the src directory
my_package_datas = collect_data_files('src')
datas.extend(my_package_datas)

# Include your YAML file using a relative path
datas.append(('./config/repos.yaml', 'config'))

# Predefined paths for PyQt6 plugins
qt_plugins_path = os.path.join(os.path.dirname(PyQt6.__file__), 'Qt6', 'plugins')

# Include the entry point of your application explicitly
datas.append((os.path.join('src', 'main.py'), '.'))

a = Analysis(
    ['src/main.py'],  # Entry point of your application
    pathex=['src'],
    binaries=binaries,
    datas=datas,
    hiddenimports=my_package_hiddenimports,
    hookspath=[],  # Specify your custom hooks directory if any
    noarchive=False,
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
    exclude_binaries=False,
    name='64All',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Strip debug symbols
    upx=True,  # Enable UPX compression
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    onefile=True
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,  # Strip debug symbols
    upx=True,  # Enable UPX compression
    upx_exclude=[],
    name='64AllCollection',
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

EXECUTABLE_FILE="$DIST_DIR/64All"
if [ ! -f "$EXECUTABLE_FILE" ]; then
    echo "Error: $EXECUTABLE_FILE was not found."
    exit 1
fi

echo "Executable created successfully at $EXECUTABLE_FILE."