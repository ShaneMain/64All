#!/bin/bash

set -e

# Define constants
DIST_DIR="../dist"
EXECUTABLE_FILE="$DIST_DIR/64All"
APPDIR="64All.AppDir"
DESKTOP_BASENAME="io.github.accountname.repositoryname"
DESKTOP_FILE="$DESKTOP_BASENAME.desktop"
APPIMAGE_TOOL="appimagetool-x86_64.AppImage"
CURRENT_DIR=$(pwd)

# Ensure that the existing built executable is present
if [ ! -f "$EXECUTABLE_FILE" ]; then
    echo "Error: $EXECUTABLE_FILE was not found."
    exit 1
fi

# Create necessary directories for AppDir structure
rm -rf $APPDIR
mkdir -p $APPDIR/usr/bin
mkdir -p $APPDIR/usr/share/applications
mkdir -p $APPDIR/usr/share/icons/hicolor/256x256/apps
mkdir -p $APPDIR/usr/share/metainfo

# Move built executable to AppDir
cp "$EXECUTABLE_FILE" $APPDIR/usr/bin/
chmod +x $APPDIR/usr/bin/64All

# Create a desktop file
cat <<EOF > $DESKTOP_FILE
[Desktop Entry]
Name=64All
Exec=/usr/bin/64All
Icon=64All
Type=Application
Categories=Utility;
Comment=64All application
EOF

# Move and symlink the desktop file
mv $DESKTOP_FILE $APPDIR/usr/share/applications/
ln -s usr/share/applications/$DESKTOP_FILE $APPDIR/$DESKTOP_FILE

# Ensure icon exists
ICON_SRC="../config/images/basedtuxicon.ico"
ICON_DEST="$APPDIR/usr/share/icons/hicolor/256x256/apps/64All.png"
ICON_TOP="$APPDIR/64All.png"

if [ ! -f "$ICON_SRC" ]; then
    echo "Error: Icon file not found at $ICON_SRC"
    exit 1
fi

cp "$ICON_SRC" "$ICON_DEST"
cp "$ICON_SRC" "$ICON_TOP" # Ensure top-level icon

# Create metadata file with updated information
METADATA_FILE="$APPDIR/usr/share/metainfo/$DESKTOP_BASENAME.appdata.xml"
cat <<EOF > $METADATA_FILE
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop">
    <id>io.github.accountname.repositoryname</id>
    <name>64All</name>
    <summary>64All application summary</summary>
    <description>
        <p>64All is a versatile tool for XYZ tasks. Use it to perform ABC and discover DEF.</p>
    </description>
    <metadata_license>CC0-1.0</metadata_license>
    <project_license>Proprietary</project_license>
    <provides>
        <binary>64All</binary>
    </provides>
    <launchable type="desktop-id">io.github.accountname.repositoryname.desktop</launchable>
    <releases>
        <release version="1.0" date="2024-09-18">
            <description>
                <p>Initial release of 64All.</p>
            </description>
        </release>
    </releases>
    <url type="bugtracker">https://example.com/issues</url>
    <url type="contact">https://example.com/contact</url>
</component>
EOF

# Commenting out the AppStream validation step
# if command -v appstreamcli &> /dev/null; then
#     appstreamcli validate $METADATA_FILE || true
# fi

# Check for appimagetool presence
if [ ! -f $APPIMAGE_TOOL ]; then
    wget "https://github.com/AppImage/AppImageKit/releases/download/continuous/$APPIMAGE_TOOL"
    chmod +x $APPIMAGE_TOOL
fi

# Extract appimagetool if FUSE is not available
if ! ./$APPIMAGE_TOOL --version &>/dev/null; then
    echo "FUSE not available, extracting appimagetool..."
    ./$APPIMAGE_TOOL --appimage-extract
    APPIMAGETOOL="./squashfs-root/AppRun"
else
    APPIMAGETOOL="./$APPIMAGE_TOOL"
fi

# Print out directory structure for debugging purposes
echo "AppDir structure before creating AppImage:"
tree $APPDIR

# Create symlink for AppRun
ln -s usr/bin/64All $APPDIR/AppRun

# Change the working directory to the parent directory of AppDir
cd $APPDIR/..

# Create AppImage with verbose output, ensuring the current working directory is the parent of AppDir
$APPIMAGETOOL --verbose "$(basename $APPDIR)" --no-appstream

echo "AppImage created successfully."

# Change back to the original working directory
cd $CURRENT_DIR