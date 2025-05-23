# WhatsApp Clone Tool

A Python utility for creating customized clones of WhatsApp and WhatsApp Business applications by modifying package names and resources in decompiled APK files.

![Version](https://img.shields.io/badge/version-2.2.0-blue)
![Python](https://img.shields.io/badge/python-3.x-green)
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

![Preview Script](https://i.imgur.com/VxlnT73.png)

This tool allows you to create modified clones of WhatsApp applications by replacing package names and resource references in `.smali` and `.xml` files from a decompiled APK. It supports both regular WhatsApp and WhatsApp Business applications.

## ✨ Features

- Creates customized clones of WhatsApp or WhatsApp Business
- Supports automatic or custom package naming
- Multi-threaded processing for faster execution
- Interactive mode with rich text interface (when using the `rich` library)
- Comprehensive logging and progress tracking

## 🔧 Prerequisites

- Python 3.x or higher
- Decompiled WhatsApp or WhatsApp Business APK (using APKTool or similar)

## Termux
```bash
pkg install python git -y
```

## 📚 Required Libraries

```bash
pip install tqdm rich
```

## 📥 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Towartz/wa-clone.git
   ```

2. Navigate to the directory:
   ```bash
   cd wa-clone
   ```

## 🚀 Usage

### Step 1: Decompile WhatsApp APK

Before using this tool, you need to decompile a WhatsApp APK file:

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

#### Interactive Mode (Recommended for beginners):
```bash
python whatsapp_clone.py
```
Follow the on-screen prompts to select options.

#### Command Line Mode:
```bash
python whatsapp_clone.py [folder_path] [options]
```

### Command Line Arguments

| Argument | Description |
|----------|-------------|
| `folder` | Path to the decompiled WhatsApp folder |
| `--whatsapp-type` | Type of WhatsApp: `1` = WhatsApp, `2` = WhatsApp Business |
| `--mode` | Operation mode: `1` = Auto (default package names), `2` = Custom |
| `--package` | New package name without 'com' (Required with `--mode 2`) |
| `--name` | New folder name (Required with `--mode 2`) |
| `--workers` | Number of worker threads (Default: 4) |
| `-h, --help` | Display help message |

### Examples

#### Run interactively:
```bash
python whatsapp_clone.py
```

#### Process WhatsApp with default settings:
```bash
python whatsapp_clone.py ./whatsapp_decompiled --whatsapp-type 1 --mode 1
```

#### Process WhatsApp with custom package name:
```bash
python whatsapp_clone.py ./whatsapp_decompiled --whatsapp-type 1 --mode 2 --package mywhatsapp --name MyWhatsApp
```

#### Process WhatsApp Business with 8 worker threads:
```bash
python whatsapp_clone.py ./whatsapp_decompiled --whatsapp-type 2 --mode 1 --workers 8
```

### Step 3: Recompile the Modified APK

After running the tool, you need to recompile the modified code back into an APK:

#### Using APKTool:
```bash
apktool b whatsapp_decompiled -o modified_whatsapp.apk
```

#### Using ApkToolM:
1. Select the modified folder
2. Choose "Build"
3. Wait for the build process to complete

### Step 4: Sign the APK

The recompiled APK needs to be signed before it can be installed:

#### Using APK Signer tools like APK Signer or ZipSigner

## ⚠️ Important Notes

- This tool is for educational purposes only
- For Cloning WhatsApp Business (com.whatsapp.w4b) still have bug

## 🔄 Workflow Summary

1. Decompile WhatsApp/WhatsApp Business APK → Get decompiled folder
2. Run WhatsApp Clone Tool → Get modified decompiled folder
3. Recompile modified folder → Get unsigned APK
4. Sign the APK → Get installable APK

## 🤝 Credits

- Original script ported from .bat and .ps1 scripts
- Python version by YouTube@66XZD (デキ)
