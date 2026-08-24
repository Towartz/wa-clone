# WhatsApp Clone Tool

Universal zero-dependency Python utility for creating customized clones of WhatsApp, WhatsApp Lite, and WhatsApp Business applications by modifying package names, provider authorities, and resources in decompiled APK files.

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

## Tutorial YouTube (Click Image below to view)

[![Tutorial: Decompile & Clone WhatsApp like GBWhatsApp](https://img.youtube.com/vi/oYjPnrckKdk/0.jpg)](https://www.youtube.com/watch?v=oYjPnrckKdk)

## 📋 Overview

This tool allows you to create modified clones of WhatsApp applications by replacing package names, Content Provider authorities, custom permissions, and resource references in `.smali` and `.xml` files from a decompiled APK. 

Supports regular WhatsApp (`com.whatsapp`), WhatsApp Lite (`com.whatsapp.litex`), WhatsApp Business (`com.whatsapp.w4b`), and pre-cloned custom WAMODs.

## ✨ Features (v3.0.0)

- **Zero External Dependencies**: Runs out-of-the-box on clean Android Termux, Windows, Linux, or macOS using only Python standard library (no `pip install` required).
- **Auto-Detect Base Package**: Automatically detects the package name directly from `AndroidManifest.xml`.
- **Content Provider Remapping**: Remaps all 11+ modern Content Provider authorities (`accountswitching`, `mlkitinitprovider`, `orbitmessages`, `orbitsso`, etc.) to prevent `INSTALL_FAILED_CONFLICTING_PROVIDER`.
- **Custom Permission Remapping**: Remaps all 9+ custom defined permissions to prevent `INSTALL_FAILED_DUPLICATE_PERMISSION`.
- **Multi-DEX Smali Support**: Recursively traverses `smali`, `smali_classes2` through `smali_classes99`.
- **Official Module Protection**: Whitelist protects Meta/WhatsApp submodules from bytecode namespace collisions.
- **Built-in Pure Python TUI**: Decorative ASCII/Unicode box panels, structured tables, and dynamic real-time progress bars.

## 🔧 Prerequisites

- Python 3.8 or higher (Zero extra pip packages required!)
- Decompiled WhatsApp APK (using APKTool or ApkToolM)

### Termux Setup:
```bash
pkg install python git -y
```

## 📥 Installation

```bash
git clone https://github.com/Towartz/wa-clone.git
cd wa-clone
```

## 🚀 Usage

### Step 1: Decompile WhatsApp APK

#### Using APKTool (Command Line):
```bash
apktool d path/to/whatsapp.apk -o whatsapp_decompiled
```

#### Using ApkToolM (Android App):
1. Open ApkToolM
2. Click on the APK file
3. Select "Decompile" option
4. Choose "Decompile all resources and all classes.dex"

### Step 2: Run the Cloning Tool

#### Interactive Mode (Recommended):
```bash
python whatsapp_clone.py
```
Follow the on-screen prompts with auto-detected package settings.

#### Command Line Mode:
```bash
python whatsapp_clone.py [folder_path] [options]
```

### Command Line Arguments

| Argument | Description |
|---|---|
| `folder` | Path to the decompiled WhatsApp folder |
| `--whatsapp-type` | Type of WhatsApp: `1` = Standard, `2` = Business, `3` = Custom/Auto |
| `--mode` | Operation mode: `1` = Auto, `2` = Custom Package, `3` = Custom ALL |
| `--package` | New package name without 'com.' (e.g. `towartz.wa`) |
| `--name` | New storage folder name (e.g. `TowartzWA`) |
| `--search-pattern` | Custom base search pattern (Mode 3 only) |
| `--workers` | Number of worker threads (Default: 8) |
| `-h, --help` | Display help message |

### Examples

```bash
# Auto-detect base package and clone with custom name
python whatsapp_clone.py ./whatsapp_decompiled --mode 2 --package mywa --name MyWA

# Process WhatsApp Business
python whatsapp_clone.py ./whatsapp_decompiled --whatsapp-type 2 --mode 1

# Process with 16 parallel worker threads
python whatsapp_clone.py ./whatsapp_decompiled --mode 2 --package mywa --name MyWA --workers 16
```

### Step 3: Recompile & Sign

1. Recompile the modified folder:
   ```bash
   apktool b whatsapp_decompiled -o modified_whatsapp.apk
   ```
2. Sign the APK using `apksigner` or ApkToolM.

## 🤝 Credits

- Original script ported from .bat and .ps1 scripts
- Python version by YouTube@66XZD
