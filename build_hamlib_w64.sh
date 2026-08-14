#!/bin/bash
set -e

echo "=== Hamlib + Python-Bindings Build-Skript (Windows/MSYS2) ==="

# -----------------------------
# 1. Konfiguration
# -----------------------------
# Fester Pfad zur Python-venv (Ziel für .pyd/DLLs)
# Beispiele:
#   /c/repos/ck-netctrl/.venv        (MSYS2-Shell)
#   C:\repos\ck-netctrl\.venv        (CMD/Powershell)
VENV_PATH="/c/repos/ck-netctrl/.venv"
PYTHON_BIN="$VENV_PATH/Scripts/python.exe"

# >>>>>>>> HIER: System-Python für Header/Libs <<<<<<<<
# Passe diese Variable an dein System an:
# Beispiele:
#   /c/Users/foo/AppData/Local/Programs/Python/Python312
#   /c/Python312
SYS_PY_HOME="/c/Users/foo/AppData/Local/Programs/Python/Python312"
SYS_PY_INCLUDE="$SYS_PY_HOME/include"
SYS_PY_LIBS="$SYS_PY_HOME/libs"

# Hamlib-Verzeichnisse
HAMLIB_SRC="$HOME/Hamlib"
HAMLIB_BUILD="$HOME/hamlib-build"
LOCAL_INSTALL="$HOME/local"

# -----------------------------
# 2. MSYS2 Build Tools prüfen
# -----------------------------
echo "[INFO] Stelle sicher, dass folgende Pakete installiert sind:"
echo "pacman -S git base-devel mingw-w64-x86_64-toolchain mingw-w64-x86_64-python"
echo "pacman -S swig automake autoconf libtool"

# -----------------------------
# 3. Hamlib klonen / bootstrap
# -----------------------------
if [ ! -d "$HAMLIB_SRC" ]; then
    echo "[INFO] Klone Hamlib..."
    git clone https://github.com/Hamlib/Hamlib.git "$HAMLIB_SRC"
fi

cd "$HAMLIB_SRC"
./bootstrap

# -----------------------------
# 4. Out-of-tree Build
# -----------------------------
mkdir -p "$HAMLIB_BUILD"
cd "$HAMLIB_BUILD"

"$HAMLIB_SRC/configure" \
    --with-python-binding PYTHON="$PYTHON_BIN" \
    --prefix="$LOCAL_INSTALL"

make -j"$(nproc)"
make install

# -----------------------------
# 5. Python-Bindings kompilieren
# -----------------------------
echo "[INFO] Kompiliere Python-Bindings..."

PY_VER=$("$PYTHON_BIN" -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')")
SITE_PACKAGES="$VENV_PATH/Lib/site-packages"
BINDINGS_DIR="$HAMLIB_BUILD/bindings"

gcc -O2 -Wall -shared \
    -I"$SYS_PY_INCLUDE" \
    -I"$HAMLIB_BUILD/include" \
    -I"$LOCAL_INSTALL/include" \
    "$BINDINGS_DIR/hamlibpy_wrap.c" \
    -L"$SYS_PY_LIBS" -lpython${PY_VER/./} \
    -L"$LOCAL_INSTALL/lib" -lhamlib \
    -o "$SITE_PACKAGES/_Hamlib.pyd"

# -----------------------------
# 6. Dateien in venv kopieren
# -----------------------------
echo "[INFO] Kopiere Hamlib.py und DLLs in venv..."

cp "$BINDINGS_DIR/Hamlib.py" "$SITE_PACKAGES/"
cp "$LOCAL_INSTALL/lib/libhamlib-4.dll" "$SITE_PACKAGES/"

# Nur libwinpthread-1.dll kopieren
MINGW_BIN="/mingw64/bin"
if [ -f "$MINGW_BIN/libwinpthread-1.dll" ]; then
    cp "$MINGW_BIN/libwinpthread-1.dll" "$SITE_PACKAGES/"
fi

# -----------------------------
# 7. Fertig
# -----------------------------
echo "=== Build abgeschlossen ==="
echo "Dateien liegen in: $SITE_PACKAGES"
echo "Test: 'source $VENV_PATH/Scripts/activate' und dann 'python -c \"import Hamlib\"'"
echo "Test: activate venv und 'import Hamlib' in Python"
