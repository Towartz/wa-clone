# WhatsApp Clone Tool

Universal zero-dependency Python utility for creating customized clones of WhatsApp, WhatsApp Lite, and WhatsApp Business applications by modifying package names, content provider authorities, custom permissions, and resources in decompiled APK files.

![Version](https://img.shields.io/badge/version-3.0.0-blue)
![Dependencies](https://img.shields.io/badge/dependencies-0%20(Pure%20Python)-brightgreen)
![Python](https://img.shields.io/badge/python-3.8+-green)

<div align="center">
  <a href="https://f-droid.org/id/packages/com.termux/">
    <img src="https://f-droid.org/repo/com.termux/en-US/icon_7jMZ7XD80oeucmGEaTwktIRZexLtGWvJfKdVD6Wu2SI=.png" width="120" height="120" alt="Termux">
    <br>
    <img src="https://f-droid.org/badge/get-it-on.png" alt="Get it on F-Droid" height="80">
  </a>
  <br>
  <b>Termux: Terminal emulator and Linux environment for Android</b>
</div>

## Tutorial YouTube

[![Tutorial: Decompile & Clone WhatsApp](https://img.youtube.com/vi/oYjPnrckKdk/0.jpg)](https://www.youtube.com/watch?v=oYjPnrckKdk)

---

## Overview

This tool allows you to create modified clones of WhatsApp applications by replacing package names, Content Provider authorities, custom permissions, and resource references in `.smali` and `.xml` files from a decompiled APK.

Supports regular WhatsApp (`com.whatsapp`), WhatsApp Lite (`com.whatsapp.litex`), WhatsApp Business (`com.whatsapp.w4b`), and pre-cloned custom WAMODs.

---

## Features

- **Zero External Dependencies**: Runs out-of-the-box on Android (Termux), Windows, Linux, and macOS using only Python standard library modules.
- **1-Click Automated Pipeline**: Accepts `.apk` or split bundles directly to decompile, remap, recompile, exact-repack, and 4-byte zipalign in a single step.
- **Split APK Bundle Merging**: Automatically merges `.apkm` (APKMirror), `.xapk` (APKPure/Combo), `.apks` (Bundletool), and split APK directories via bundled `APKEditor.jar`.
- **Bundled Cross-Platform Tools Suite**: Includes `apktool.jar` (v3.0.3), `apksigner.jar` (Build-Tools v37.0.0), `APKEditor.jar` (v1.4.9), and `d8.jar` in `./tools/`.
- **Automatic Tool Updates**: In-memory inspection and 1-click upgrade engine (`--check-tools` / `--update-tools`) querying upstream GitHub releases.
- **Touch Screen & Mouse Navigation**: ANSI SGR 1006 mouse tracking supporting touch screen taps (Termux Android) and mouse clicks (VSCode / Windows Terminal), alongside full keyboard controls.
- **Build-Only Mode**: Bypass Dalvik bytecode and XML processing (`--build-only`) to quickly recompile and repack existing decompiled folders.
- **Dedicated Distribution Folder**: Automatically routes final cloned APKs to `./dist/` and purges temporary build staging files.
- **Content Provider Remapping**: Remaps 11+ Content Provider authorities (`accountswitching`, `mlkitinitprovider`, `orbitmessages`, etc.) preventing `INSTALL_FAILED_CONFLICTING_PROVIDER`.
- **Custom Permission Remapping**: Remaps custom defined permissions preventing `INSTALL_FAILED_DUPLICATE_PERMISSION`.
- **Multi-DEX Smali Traversal**: Recursively processes `smali`, `smali_classes2` through `smali_classes99`.
- **Official Module Protection**: Whitelist protects official Meta and WhatsApp submodules from namespace collision.

---

## Prerequisites

- Python 3.8 or higher
- Java Runtime Environment (JRE) for executing tool JARs

### Termux Setup:
```bash
pkg update && pkg install python git openjdk-17 -y
```

---

## Installation

```bash
git clone https://github.com/Towartz/wa-clone.git
cd wa-clone
```

---

## Usage

### Interactive Mode (Recommended)
```bash
python whatsapp_clone.py
```
Automatically scans the directory for APKs, split bundles, and decompiled targets, presenting a menu with touch, mouse, and keyboard navigation.

### Command Line Mode

#### 1. 1-Click Automated Split Bundle or APK Cloning
```bash
# Clone directly from an APKM split bundle
python whatsapp_clone.py WhatsApp.apkm --mode 2 --package mywa --name MyWA

# Clone directly from a standard base.apk
python whatsapp_clone.py base.apk --mode 2 --package mywa --name MyWA
```

#### 2. Clone Pre-Decompiled Directory
```bash
python whatsapp_clone.py ./decompiled_base --mode 2 --package mywa --name MyWA --build --base-apk base.apk
```

#### 3. Build-Only Fast Repack (Skip Cloning)
```bash
python whatsapp_clone.py ./decompiled_base --build-only --base-apk base.apk
```

#### 4. Split Bundle Merging Only
```bash
python whatsapp_clone.py WhatsApp.apkm --merge-only
```

#### 5. Check and Upgrade Tool JARs
```bash
# Check version status against GitHub releases
python whatsapp_clone.py --check-tools

# Download and upgrade tool JARs to latest releases
python whatsapp_clone.py --update-tools
```

---

## Command Line Options

| Option | Description |
|---|---|
| `folder` | Path to root decompiled directory, `.apk` file, or split bundle (`.apkm`, `.xapk`, `.apks`) |
| `--whatsapp-type INT` | `1` = Standard WhatsApp, `2` = WhatsApp Business, `3` = Custom/Auto |
| `--mode INT` | `1` = Auto, `2` = Custom Package, `3` = Custom ALL, `4` = Build-Only |
| `--package STRING` | New package name without `com.` prefix (e.g. `towartz.wa`) |
| `--name STRING` | New storage folder name (e.g. `TowartzWA`) |
| `--search-pattern STRING` | Custom base search pattern to replace (Mode 3 only) |
| `--build` | Recompile with Apktool and package final 1:1 exact ZIP APK |
| `--build-only` | Skip cloning and repack decompiled folder directly |
| `--merge-only` | Merge split bundle into standalone APK and exit |
| `--base-apk FILE` | Path to base.apk template for 1:1 direct-copy repack |
| `--out-dir DIR` | Directory for output APKs (Default: `dist`) |
| `--out-apk FILE` | Custom output path for final cloned APK |
| `--sign` | Sign the output APK with apksigner (Default: unsigned) |
| `--keystore FILE` | Keystore path for signing |
| `--clean` | Force clean re-decompilation if folder exists |
| `--check-tools` | Check GitHub releases for tool updates |
| `--update-tools` | Automatically update tool JARs to latest releases |
| `-h, --help` | Display help message |

---

## Configuration (`config.txt`)

You can customize tool paths and execution behavior in `config.txt`:

```ini
APKTOOL_PATH=tools\apktool.jar
APKSIGNER_PATH=tools\apksigner.jar
SEVEN_ZIP_PATH=C:\Windows\system32\7z.exe
ZIPALIGN_PATH=C:\Android\build-tools\35.0.0\zipalign.exe
AUTO_SIGN=false
OUTPUT_DIR=dist
AUTO_CLEAN_BUILD=true
CHECK_TOOL_UPDATES=false
DEFAULT_WORKERS=12
```

---

## Credits

- Python version by YouTube@66XZD
