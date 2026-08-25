#!/usr/bin/env python3
"""
WhatsApp Clone Tool

This script allows cloning WhatsApp, WhatsApp Lite, WhatsApp Business,
or custom WAMOD applications by modifying package names, content provider authorities,
custom permissions, and resources in .smali and .xml files.

Zero external dependencies (100% pure Python standard library).

Usage:
    python whatsapp_clone.py [folder_path] [options]
    python whatsapp_clone.py -h/--help

Author: Python by YouTube@66XZD
Version: 3.0.0 (Zero Dependencies Edition)
"""

import os
import sys
import re
import glob
import time
import shutil
import zipfile
import subprocess
import argparse
from typing import List, Tuple, Optional, Dict
from concurrent.futures import ThreadPoolExecutor

# UTF-8 Encoding Setup for Windows/Termux/Linux
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


class TerminalUI:
    """Built-in pure Python Terminal UI with ANSI color styling and box formatters."""
    
    # ANSI Colors
    RESET = "[0m"
    BOLD = "[1m"
    DIM = "[2m"
    CYAN = "[96m"
    GREEN = "[92m"
    YELLOW = "[93m"
    RED = "[91m"
    MAGENTA = "[95m"
    BLUE = "[94m"
    WHITE = "[97m"
    
    @classmethod
    def supports_color(cls) -> bool:
        """Checks if the terminal environment supports ANSI color codes."""
        if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
            return False
        if os.name == "nt":
            return os.environ.get("TERM") is not None or "WT_SESSION" in os.environ or (hasattr(sys, 'getwindowsversion') and sys.getwindowsversion().build >= 10586)
        return True

    @classmethod
    def supports_unicode(cls) -> bool:
        """Checks if stdout can encode Unicode box characters."""
        try:
            encoding = getattr(sys.stdout, "encoding", "utf-8") or "utf-8"
            "╭─█✓".encode(encoding)
            return True
        except Exception:
            return False

    @classmethod
    def colorize(cls, text: str, color_code: str) -> str:
        if cls.supports_color():
            return f"{color_code}{text}{cls.RESET}"
        return text

    @classmethod
    def print_panel(cls, title: str, subtitle: str, lines: List[str], border_color: str = CYAN) -> None:
        """Renders a structured decorative panel box."""
        use_unicode = cls.supports_unicode()
        tl = "╭" if use_unicode else "+"
        tr = "╮" if use_unicode else "+"
        bl = "╰" if use_unicode else "+"
        br = "╯" if use_unicode else "+"
        h = "─" if use_unicode else "-"
        v = "│" if use_unicode else "|"

        clean_lines = [re.sub(r'\033\[[0-9;]*m', '', line) for line in lines]
        max_len = max([len(line) for line in clean_lines] + [len(title) + 4, len(subtitle) + 4, 50])
        box_width = max_len + 4

        top_border = f"{tl}{h} {cls.colorize(title, cls.BOLD + border_color)} " + h * (box_width - len(title) - 5) + tr
        bottom_border = bl + h * (box_width - len(subtitle) - 5) + f" {cls.colorize(subtitle, cls.DIM + border_color)} {h}{br}"

        print(top_border)
        for line in lines:
            raw_len = len(re.sub(r'\033\[[0-9;]*m', '', line))
            padding = " " * (box_width - raw_len - 2)
            print(f"{v} {line}{padding}{v}")
        print(bottom_border)

    @classmethod
    def print_table(cls, title: str, headers: List[str], rows: List[List[str]]) -> None:
        """Renders an ASCII / Unicode formatted table."""
        use_unicode = cls.supports_unicode()
        tl = "┌" if use_unicode else "+"
        tr = "┐" if use_unicode else "+"
        bl = "└" if use_unicode else "+"
        br = "┘" if use_unicode else "+"
        cross = "┼" if use_unicode else "+"
        top_t = "┬" if use_unicode else "-"
        bot_t = "┴" if use_unicode else "-"
        left_t = "├" if use_unicode else "+"
        right_t = "┤" if use_unicode else "+"
        h = "─" if use_unicode else "-"
        v = "│" if use_unicode else "|"

        num_cols = len(headers)
        col_widths = [len(h_name) for h_name in headers]
        
        for row in rows:
            for i in range(num_cols):
                clean_cell = re.sub(r'\033\[[0-9;]*m', '', str(row[i]))
                if len(clean_cell) > col_widths[i]:
                    col_widths[i] = len(clean_cell)
                    
        total_width = sum(col_widths) + (3 * num_cols) + 1
        
        # Header Box
        print(f"{tl}{h} {cls.colorize(title, cls.BOLD + cls.CYAN)} " + h * (total_width - len(title) - 5) + tr)
        
        # Column Names
        header_line = f"{v} " + f" {v} ".join([cls.colorize(headers[i].ljust(col_widths[i]), cls.BOLD + cls.WHITE) for i in range(num_cols)]) + f" {v}"
        print(header_line)
        
        sep_line = left_t + cross.join([h * (w + 2) for w in col_widths]) + right_t
        print(sep_line)
        
        # Rows
        for row in rows:
            row_line = f"{v} "
            for i in range(num_cols):
                raw_cell = str(row[i])
                clean_len = len(re.sub(r'\033\[[0-9;]*m', '', raw_cell))
                pad = " " * (col_widths[i] - clean_len)
                row_line += f"{raw_cell}{pad} {v} "
            print(row_line[:-1])
            
        # Bottom
        print(bl + bot_t.join([h * (w + 2) for w in col_widths]) + br)


def render_progress_bar(task_name: str, current: int, total: int, start_time: float, bar_width: int = 20) -> None:
    """Renders a single-line dynamic real-time progress bar without spamming."""
    if total <= 0:
        return
    use_unicode = TerminalUI.supports_unicode()
    fill_char = "█" if use_unicode else "#"
    empty_char = "░" if use_unicode else "-"

    percent = (current / total) * 100.0
    filled = int(bar_width * current // total)
    bar = fill_char * filled + empty_char * (bar_width - filled)
    
    elapsed = max(time.time() - start_time, 0.001)
    rate = current / elapsed
    eta = (total - current) / rate if rate > 0 else 0
    
    elapsed_str = time.strftime("%M:%S", time.gmtime(elapsed))
    eta_str = time.strftime("%M:%S", time.gmtime(eta))
    
    # Clean single-line update with fixed width and trailing space clearing
    short_task = f"{task_name[:14]:<14}"
    msg = f"\r  {TerminalUI.colorize(short_task, TerminalUI.CYAN)} [{TerminalUI.colorize(bar, TerminalUI.GREEN)}] {percent:5.1f}% ({current}/{total}) [{elapsed_str}<{eta_str}, {rate:.0f}it/s]   \r"
    sys.stdout.write(msg)
    sys.stdout.flush()
    if current >= total:
        sys.stdout.write(f"\r  {TerminalUI.colorize(short_task, TerminalUI.CYAN)} [{TerminalUI.colorize(bar, TerminalUI.GREEN)}] 100.0% ({total}/{total}) [{elapsed_str}, {rate:.0f}it/s]   \n")
        sys.stdout.flush()


class TerminalInput:
    """Zero-dependency cross-platform raw input and ANSI mouse tracking controller."""
    
    @staticmethod
    def is_interactive() -> bool:
        return hasattr(sys.stdin, "isatty") and sys.stdin.isatty() and hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
        
    @staticmethod
    def enable_mouse_tracking() -> None:
        if TerminalInput.is_interactive():
            try:
                # Enable X10 + SGR extended mouse tracking and hide cursor
                sys.stdout.write("\033[?1000h\033[?1006h\033[?25l")
                sys.stdout.flush()
            except Exception:
                pass
                
    @staticmethod
    def disable_mouse_tracking() -> None:
        if TerminalInput.is_interactive():
            try:
                # Disable mouse tracking and restore cursor
                sys.stdout.write("\033[?1000l\033[?1006l\033[?25h")
                sys.stdout.flush()
            except Exception:
                pass

    @staticmethod
    def get_event() -> Tuple[str, any]:
        """
        Reads next user input event (Keystroke or Touch/Mouse click).
        Returns tuple: ('KEY_UP'|'KEY_DOWN'|'KEY_ENTER'|'KEY_NUM'|'KEY_QUIT'|'MOUSE_CLICK'|'CHAR', value)
        """
        if not TerminalInput.is_interactive():
            line = sys.stdin.readline().strip()
            return ('LINE', line)
            
        if os.name == 'nt':
            import msvcrt
            ch = msvcrt.getwch()
            if ch in ('\x00', '\xe0'):
                ch2 = msvcrt.getwch()
                if ch2 == 'H': return ('KEY_UP', None)
                if ch2 == 'P': return ('KEY_DOWN', None)
                if ch2 == 'K': return ('KEY_LEFT', None)
                if ch2 == 'M': return ('KEY_RIGHT', None)
            elif ch == '\x1b':
                seq = ""
                start = time.time()
                while time.time() - start < 0.05:
                    if msvcrt.kbhit():
                        seq += msvcrt.getwch()
                    else:
                        time.sleep(0.005)
                if seq.startswith('[<'):
                    m = re.match(r'\[<(\d+);(\d+);(\d+)([Mm])', seq)
                    if m:
                        btn, x, y, act = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
                        if act == 'M' and btn == 0:  # Left click / touch tap
                            return ('MOUSE_CLICK', (x, y))
                elif seq in ('[A', 'OA'): return ('KEY_UP', None)
                elif seq in ('[B', 'OB'): return ('KEY_DOWN', None)
                elif seq in ('[C', 'OC'): return ('KEY_RIGHT', None)
                elif seq in ('[D', 'OD'): return ('KEY_LEFT', None)
                return ('ESC', None)
            elif ch in ('\r', '\n', ' '):
                return ('KEY_ENTER', None)
            elif ch == '\x03': # Ctrl+C
                raise KeyboardInterrupt()
            elif ch in '123456789':
                return ('KEY_NUM', int(ch))
            elif ch in ('q', 'Q'):
                return ('KEY_QUIT', None)
            elif ch in ('k', 'K'):
                return ('KEY_UP', None)
            elif ch in ('j', 'J'):
                return ('KEY_DOWN', None)
            return ('CHAR', ch)
        else:
            import tty, termios, select
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
                if ch == '\x1b':
                    seq = ""
                    start = time.time()
                    while time.time() - start < 0.05:
                        r, _, _ = select.select([sys.stdin], [], [], 0.01)
                        if r:
                            seq += sys.stdin.read(1)
                        else:
                            break
                    if seq.startswith('[<'):
                        m = re.match(r'\[<(\d+);(\d+);(\d+)([Mm])', seq)
                        if m:
                            btn, x, y, act = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
                            if act == 'M' and btn == 0:
                                return ('MOUSE_CLICK', (x, y))
                    elif seq in ('[A', 'OA'): return ('KEY_UP', None)
                    elif seq in ('[B', 'OB'): return ('KEY_DOWN', None)
                    elif seq in ('[C', 'OC'): return ('KEY_RIGHT', None)
                    elif seq in ('[D', 'OD'): return ('KEY_LEFT', None)
                    return ('ESC', None)
                elif ch in ('\r', '\n', ' '):
                    return ('KEY_ENTER', None)
                elif ch == '\x03':
                    raise KeyboardInterrupt()
                elif ch in '123456789':
                    return ('KEY_NUM', int(ch))
                elif ch in ('q', 'Q'):
                    return ('KEY_QUIT', None)
                elif ch in ('k', 'K'):
                    return ('KEY_UP', None)
                elif ch in ('j', 'J'):
                    return ('KEY_DOWN', None)
                return ('CHAR', ch)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


class InteractiveMenu:
    """Interactive touch/mouse-clickable and keyboard-navigable menu renderer."""

    @classmethod
    def select(cls, title: str, options: List[Tuple[str, str]], default_index: int = 0, help_hint: str = "Tap/Click item or use ↑/↓ Arrow keys, Numbers, Enter") -> int:
        """
        Renders an interactive touch/clickable menu.
        Returns the chosen 0-based option index.
        """
        if not options:
            return 0
        if not TerminalInput.is_interactive():
            print(f"\n{TerminalUI.colorize(title, TerminalUI.BOLD + TerminalUI.CYAN)}")
            for idx, (label, desc) in enumerate(options, 1):
                desc_str = f" ({desc})" if desc else ""
                print(f"  {idx}. {label}{desc_str}")
            try:
                ans = input(f"Select [1-{len(options)}, default: {default_index+1}]: ").strip()
                val = int(ans)
                if 1 <= val <= len(options):
                    return val - 1
            except (EOFError, Exception):
                pass
            return default_index

        TerminalInput.enable_mouse_tracking()
        selected_idx = max(0, min(default_index, len(options) - 1))
        rendered_lines_count = 0
        
        try:
            while True:
                lines = []
                lines.append(f"{TerminalUI.colorize('┌─', TerminalUI.CYAN)} {TerminalUI.colorize(title, TerminalUI.BOLD + TerminalUI.CYAN)}")
                lines.append(f"{TerminalUI.colorize('│', TerminalUI.CYAN)} {TerminalUI.colorize(help_hint, TerminalUI.DIM)}")
                lines.append(f"{TerminalUI.colorize('├───────────────────────────────────────────────────', TerminalUI.CYAN)}")
                
                for idx, (label, desc) in enumerate(options):
                    num_badge = f"[{idx + 1}]"
                    desc_str = f" - {TerminalUI.colorize(desc, TerminalUI.DIM)}" if desc else ""
                    if idx == selected_idx:
                        pointer = TerminalUI.colorize(" ➤ ", TerminalUI.BOLD + TerminalUI.GREEN)
                        item_text = f"{TerminalUI.colorize(num_badge, TerminalUI.BOLD + TerminalUI.YELLOW)} {TerminalUI.colorize(label, TerminalUI.BOLD + TerminalUI.WHITE)}{desc_str}"
                    else:
                        pointer = "   "
                        item_text = f"{TerminalUI.colorize(num_badge, TerminalUI.DIM)} {TerminalUI.colorize(label, TerminalUI.WHITE)}{desc_str}"
                    lines.append(f"{TerminalUI.colorize('│', TerminalUI.CYAN)}{pointer}{item_text}")
                
                lines.append(f"{TerminalUI.colorize('└───────────────────────────────────────────────────', TerminalUI.CYAN)}")
                
                if rendered_lines_count > 0:
                    sys.stdout.write(f"\033[{rendered_lines_count}A\r")
                
                for line in lines:
                    sys.stdout.write(f"\033[2K{line}\n")
                sys.stdout.flush()
                rendered_lines_count = len(lines)
                
                event_type, event_val = TerminalInput.get_event()
                
                if event_type == 'KEY_UP':
                    selected_idx = (selected_idx - 1) % len(options)
                elif event_type == 'KEY_DOWN':
                    selected_idx = (selected_idx + 1) % len(options)
                elif event_type == 'KEY_NUM':
                    if 1 <= event_val <= len(options):
                        selected_idx = event_val - 1
                        break
                elif event_type in ('KEY_ENTER', 'KEY_QUIT', 'ESC'):
                    break
                elif event_type == 'MOUSE_CLICK':
                    break
        finally:
            TerminalInput.disable_mouse_tracking()
            sys.stdout.write("\n")
            sys.stdout.flush()
            
        return selected_idx

    @classmethod
    def confirm(cls, prompt_text: str, default: bool = True) -> bool:
        """Interactive touch/clickable [ Yes ] / [ No ] buttons."""
        if not TerminalInput.is_interactive():
            try:
                ans = input(f"{prompt_text} ({'Y/n' if default else 'y/N'}): ").strip().lower()
                if not ans:
                    return default
                return ans in ('y', 'yes')
            except (EOFError, Exception):
                return default
            
        options = [
            ("Yes", "Proceed with build & repack"),
            ("No", "Skip and leave ready for manual compilation")
        ]
        chosen = cls.select(prompt_text, options, default_index=0 if default else 1)
        return (chosen == 0)


# Whitelist of official Meta / WhatsApp submodules whose class bytecode namespaces should remain un-renamed
OFFICIAL_MODULES = (
    "aborthooks|accesslibraryprovider|accountswitching|adscreation|anr|audioRecording|"
    "backup|bloks|breakpad|calling|companiondevice|crossapp|executorch|fieldstats|filter|"
    "foa|garmin|gwpasan|infra|instrumentation|jid|litex|media|messagedrafts|messagetranslation|"
    "mlkit|music|MusicApi|NativeMediaHandler|nativelibloader|ohai|orbit|pixel|productinfra|"
    "protocol|pytorch|stickers|superpack|unity|util|voicetranscription|voipcalling|wfl|"
    "wamsys|WaOhaiClient|waquickpromotionclient|AppShell|GifHelper|Mp4Ops|SmbAppShell|"
    "SqliteShell|StickyHeadersRecyclerView|VideoFrameConverter"
)


def show_help():
    help_text = """
WhatsApp Clone Tool Help Guide (v3.0.0 - Zero Deps)
==================================================

DESCRIPTION:
    This tool allows you to create modified clones of WhatsApp, WhatsApp Lite,
    WhatsApp Business, or custom WAMODs by modifying package names, provider
    authorities, custom permissions, and resources in decompiled APK directories.

USAGE:
    python whatsapp_clone.py [folder_or_apk_path] [options]
    python whatsapp_clone.py -h/--help

ARGUMENTS:
    folder_or_apk         The root folder of decompiled code OR a .apk file.
                          If an APK file is provided, it is automatically decompiled,
                          cloned, and repacked into a ready-to-sign cloned APK.
                          If not provided, you'll be prompted interactively.

OPTIONS:
    --whatsapp-type INT   Specify WhatsApp type:
                          1 = Standard WhatsApp (com.whatsapp / com.whatsapp.litex)
                          2 = WhatsApp Business (com.whatsapp.w4b)
                          3 = Custom Base / Auto-Detect from Manifest

    --mode INT            Select operation mode:
                          1 = Auto (uses default package names)
                          2 = Custom Base to Clone (specify custom package name)
                          3 = Custom ALL (Clone of Cloned Base with custom search pattern)

    --package STRING      New package name without 'com.' prefix (e.g. 'towartz.wa')
                          (Required with --mode 2 or 3)

    --name STRING         New storage folder name (e.g. 'TowartzWA')
                          (Required with --mode 2 or 3)
                          
    --search-pattern STRING Custom base search pattern (e.g. 'com.whatsapp' or 'com.whatsapp.litex')
                          (Only with --mode 3)

    --workers INT         Number of worker threads for parallel processing
                          (Default from config: 12)

    --build               Automatically recompile with Apktool and package final cloned APK
                          (Enabled automatically if input is an APK file)
    --base-apk FILE       Path to original base.apk template for 1:1 direct-copy exact ZIP repack
    --out-apk FILE        Output path for final APK (default: <package>_ExactZip_cloned.apk)
    --sign                Sign the output APK with apksigner (Default: unsigned)
    --keystore FILE       Path to .jks keystore for signing (default: auto-detected)

    -h, --help            Display this help message

EXAMPLES:
    # 1-Click Fully Automated: Decompile base.apk, clone, and package output APK
    python whatsapp_clone.py base.apk --mode 2 --package mywa --name MyWA

    # Clone already-decompiled folder and build unsigned exact ZIP APK
    python whatsapp_clone.py ./decompiled_apk --mode 2 --package mywa --name MyWA --build --base-apk base.apk

    # Process WhatsApp Business APK
    python whatsapp_clone.py w4b_base.apk --whatsapp-type 2 --mode 1

    # Run interactively (will guide you step-by-step with auto-detection)
    python whatsapp_clone.py

NOTES:
    - Automatically remaps 11+ Content Provider authorities to prevent INSTALL_FAILED_CONFLICTING_PROVIDER.
    - Automatically remaps custom defined permissions to prevent INSTALL_FAILED_DUPLICATE_PERMISSION.
    - Handles all multi-DEX smali folders (smali, smali_classes2 .. smali_classes99).
"""
    print(help_text)
    sys.exit(0)


class WhatsAppCloneConfig:
    
    def __init__(self):
        self.root_folder: str = ""
        self.detected_base_pkg: str = "com.whatsapp"
        self.current_folder_name: str = "WhatsApp"
        self.new_package_name: str = ""
        self.new_folder_name: str = ""
        self.new_package_name_path: str = ""
        self.custom_search_pattern: str = ""
        self.max_workers: int = 8
        
    def detect_from_manifest(self) -> Tuple[str, str]:
        """Detects the base package and app type from AndroidManifest.xml if available."""
        manifest_path = os.path.join(self.root_folder, "AndroidManifest.xml")
        if os.path.isfile(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                pkg_match = re.search(r'package="([^"]+)"', content)
                if pkg_match:
                    self.detected_base_pkg = pkg_match.group(1)
                    if "w4b" in self.detected_base_pkg.lower() or "business" in self.detected_base_pkg.lower():
                        self.current_folder_name = "WhatsApp Business"
                    else:
                        self.current_folder_name = "WhatsApp"
                    return self.detected_base_pkg, self.current_folder_name
            except Exception:
                pass
        return self.detected_base_pkg, self.current_folder_name

    def display_config(self) -> None:
        headers = ["Parameter", "Configured Value"]
        rows = [
            ["Root folder", TerminalUI.colorize(self.root_folder, TerminalUI.GREEN)],
            ["Detected base package", TerminalUI.colorize(self.detected_base_pkg, TerminalUI.YELLOW)],
            ["Current folder name", self.current_folder_name],
            ["New package name", TerminalUI.colorize(f"com.{self.new_package_name}", TerminalUI.GREEN)],
            ["New folder name", self.new_folder_name],
            ["Package path format", f"com/{self.new_package_name_path}"],
            ["Worker threads", str(self.max_workers)],
        ]
        if self.custom_search_pattern:
            rows.append(["Custom search pattern", self.custom_search_pattern])
        TerminalUI.print_table("Configuration Parameters", headers, rows)


class FileProcessor:
    
    def __init__(self, config: WhatsAppCloneConfig):
        self.config = config
        
    def get_files(self) -> List[str]:
        raise NotImplementedError("Subclasses must implement get_files()")
        
    def process_file(self, file_path: str) -> bool:
        raise NotImplementedError("Subclasses must implement process_file()")
    
    def process_all_files(self) -> Tuple[int, int]:
        files = self.get_files()
        if not files:
            print(TerminalUI.colorize(f"  [-] No {self.__class__.__name__} files found to process.", TerminalUI.DIM))
            return 0, 0
        
        total_files = len(files)
        success_count = 0
        start_time = time.time()
        last_update_time = 0.0
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            for idx, result in enumerate(executor.map(self.process_file, files), 1):
                if result:
                    success_count += 1
                now = time.time()
                if (now - last_update_time >= 0.08) or idx == total_files:
                    render_progress_bar(self.__class__.__name__, idx, total_files, start_time)
                    last_update_time = now
                    
        return total_files, success_count


class SmaliProcessor(FileProcessor):
    
    def __init__(self, config: WhatsAppCloneConfig):
        super().__init__(config)
        
        if hasattr(self.config, 'custom_search_pattern') and self.config.custom_search_pattern:
            base_dot = self.config.custom_search_pattern
        else:
            base_dot = self.config.detected_base_pkg

        base_slash = base_dot.replace('.', '/')
        new_dot = f"com.{self.config.new_package_name}"
        new_slash = f"com/{self.config.new_package_name_path}"

        self.pattern_dot = re.compile(re.escape(base_dot))
        self.pattern_slash = re.compile(re.escape(base_slash))
        self.new_dot = new_dot
        self.new_slash = new_slash

        self.official_dot_pattern = re.compile(
            r'(\.)' + re.escape(self.config.new_package_name) + r'(\.)(' + OFFICIAL_MODULES + r')'
        )
        self.official_slash_pattern = re.compile(
            r'(\.|/)' + re.escape(self.config.new_package_name_path) + r'(\.|/)(' + OFFICIAL_MODULES + r')'
        )
    
    def get_files(self) -> List[str]:
        smali_files = []
        for root, dirs, files in os.walk(self.config.root_folder):
            dirs[:] = [d for d in dirs if d not in ('build', '.cache', '.git', 'dist')]
            for f in files:
                if f.endswith(".smali"):
                    smali_files.append(os.path.join(root, f))
        return smali_files
        
    def process_file(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            
            # Step 1: Replace slash-separated class paths (e.g. Lcom/whatsapp/... -> Lcom/new_pkg/...)
            content = self.pattern_slash.sub(self.new_slash, content)
            
            # Step 2: Replace dot-separated package identifiers
            content = self.pattern_dot.sub(self.new_dot, content)
            
            # Step 3: Revert official Meta/WhatsApp internal modules back to official namespaces for class bytecode
            if "Business" in self.config.current_folder_name:
                content = self.official_dot_pattern.sub(r'\1whatsapp.w4b\2\3', content)
                content = self.official_slash_pattern.sub(r'\1whatsapp/w4b\2\3', content)
            else:
                content = self.official_dot_pattern.sub(r'\1whatsapp\2\3', content)
                content = self.official_slash_pattern.sub(r'\1whatsapp\2\3', content)
            
            # Step 4: Protect provider authority and custom permission strings in Smali from duplicate collisions
            content = re.sub(
                r'("com\.whatsapp(?:\.w4b)?\.(?:orbit|mlkit|accesslibraryprovider|accountswitching|backup|pixel)[^"]*")',
                lambda m: m.group(1).replace("com.whatsapp", self.new_dot),
                content
            )
            
            # Step 5: Normalize any double package occurrences
            double_pkg_dot = f"{self.new_dot}.{self.config.new_package_name}"
            double_pkg_slash = f"{self.new_slash}/{self.config.new_package_name_path}"
            content = content.replace(double_pkg_dot, self.new_dot)
            content = content.replace(double_pkg_slash, self.new_slash)
            
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            return True
                
        except Exception:
            return False


class XmlProcessor(FileProcessor):
    
    def __init__(self, config: WhatsAppCloneConfig):
        super().__init__(config)
        
        if hasattr(self.config, 'custom_search_pattern') and self.config.custom_search_pattern:
            self.base_pkg = self.config.custom_search_pattern
        else:
            self.base_pkg = self.config.detected_base_pkg

        self.new_pkg = f"com.{self.config.new_package_name}"
        self.folder_pattern = re.compile(re.escape(self.config.current_folder_name))
        self.package_pattern = re.compile(re.escape(self.base_pkg))
        
        # Universal XML whitelist pattern for tag names (<com.whatsapp.<mod>), attributes (="com.whatsapp.<mod>"), etc.
        self.official_xml_pattern = re.compile(
            r'([<"\'/])' + re.escape(self.new_pkg) + r'(\.)(' + OFFICIAL_MODULES + r')'
        )
        
    def get_files(self) -> List[str]:
        xml_files = []
        for root, dirs, files in os.walk(self.config.root_folder):
            dirs[:] = [d for d in dirs if d not in ('build', '.cache', '.git', 'dist')]
            for f in files:
                if f.endswith(".xml"):
                    xml_files.append(os.path.join(root, f))
        return xml_files
        
    def process_file(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            
            # Step 1: Replace all occurrences of base_pkg with new_pkg (manifest, components, authorities, permissions)
            content = self.package_pattern.sub(self.new_pkg, content)
            
            # Step 2: Universal XML whitelist reversion for tags (<com.whatsapp.<mod>), attributes, and target activities
            if "Business" in self.config.current_folder_name:
                content = self.official_xml_pattern.sub(r'\1com.whatsapp.w4b\2\3', content)
            else:
                content = self.official_xml_pattern.sub(r'\1com.whatsapp\2\3', content)
            
            # Step 3: GUARANTEE that all Provider Authorities and Custom Permissions stay on the CLONED package name!
            # (Prevents INSTALL_FAILED_DUPLICATE_PERMISSION and INSTALL_FAILED_CONFLICTING_PROVIDER)
            # 3a. Authorities
            content = re.sub(
                r'(android:authorities=")(?:com\.whatsapp(?:\.w4b)?(?:\.' + re.escape(self.config.new_package_name) + r')?|' + re.escape(self.new_pkg) + r')(\.[^"]*")',
                r'\1' + self.new_pkg + r'\2',
                content
            )
            # 3b. Declared permissions & uses-permissions
            content = re.sub(
                r'(<(?:permission|uses-permission)[^>]*android:name=")(?:com\.whatsapp(?:\.w4b)?(?:\.' + re.escape(self.config.new_package_name) + r')?|' + re.escape(self.new_pkg) + r')(\.[^"]*")',
                r'\1' + self.new_pkg + r'\2',
                content
            )
            # 3c. Component permission attributes
            content = re.sub(
                r'(android:(?:permission|readPermission|writePermission)=")(?:com\.whatsapp(?:\.w4b)?(?:\.' + re.escape(self.config.new_package_name) + r')?|' + re.escape(self.new_pkg) + r')(\.[^"]*")',
                r'\1' + self.new_pkg + r'\2',
                content
            )
            
            # 3d. Normalize any double package occurrences
            double_pkg = f"{self.new_pkg}.{self.config.new_package_name}"
            content = content.replace(double_pkg, self.new_pkg)
            
            # Step 4: Preserve official external package queries in <queries>
            content = re.sub(
                r'(<package\s+android:name=")' + re.escape(self.new_pkg) + r'(\.w4b"/>)',
                r'\1com.whatsapp\2',
                content
            )
            
            # Step 5: Remap Storage Folders (e.g. filepaths.xml)
            content = self.folder_pattern.sub(self.config.new_folder_name, content)
            
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
                
            return True
                
        except Exception:
            return False


class ToolConfig:
    """Manages configuration from config.txt, Environment variables, and OS auto-detection."""
    
    _config_cache: Optional[Dict[str, str]] = None
    _config_file_path: Optional[str] = None
    
    @classmethod
    def get_config_path(cls) -> str:
        if cls._config_file_path:
            return cls._config_file_path
        
        candidates = [
            os.path.join(os.getcwd(), "config.txt"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.txt")
        ]
        for c in candidates:
            if os.path.exists(c):
                cls._config_file_path = c
                return c
                
        cls._config_file_path = candidates[0]
        return cls._config_file_path

    @classmethod
    def load(cls) -> Dict[str, str]:
        if cls._config_cache is not None:
            return cls._config_cache
            
        cfg = {}
        cfg_file = cls.get_config_path()
        
        if os.path.exists(cfg_file):
            try:
                with open(cfg_file, 'r', encoding='utf-8-sig', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#') or line.startswith(';'):
                            continue
                        if '=' in line:
                            key, val = line.split('=', 1)
                            key = key.strip().upper()
                            val = val.strip().strip('"').strip("'")
                            if val:
                                cfg[key] = val
            except Exception:
                pass
        
        cls._config_cache = cfg
        return cfg

    @classmethod
    def get(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        cfg = cls.load()
        key_upper = key.upper()
        # 1. config.txt
        if key_upper in cfg and cfg[key_upper]:
            return cfg[key_upper]
        # 2. Environment Variable
        if key_upper in os.environ and os.environ[key_upper]:
            return os.environ[key_upper]
        return default

    @classmethod
    def find_tool(cls, tool_key: str) -> Optional[str]:
        """
        Resolves tool path via:
        1. config.txt (e.g. APKTOOL_PATH)
        2. Environment variable (e.g. APKTOOL_PATH, ANDROID_HOME)
        3. Dynamic Android SDK & OS path detection (Windows, Linux, macOS, Termux)
        4. System PATH via shutil.which
        """
        configured_path = cls.get(f"{tool_key}_PATH") or cls.get(tool_key)
        if configured_path and os.path.exists(configured_path):
            return configured_path
            
        tool_name = tool_key.lower().replace("_path", "").replace("seven_zip", "7z")
        
        android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
        sdk_candidates = []
        if android_home and os.path.isdir(android_home):
            build_tools_dir = os.path.join(android_home, "build-tools")
            if os.path.isdir(build_tools_dir):
                for version_dir in sorted(os.listdir(build_tools_dir), reverse=True):
                    sdk_candidates.append(os.path.join(build_tools_dir, version_dir))

        common_locations = {
            "7z": [
                r"C:\Windows\system32\7z.exe",
                r"C:\Program Files\7-Zip\7z.exe",
                r"C:\Program Files (x86)\7-Zip\7z.exe",
                "/usr/bin/7z",
                "/usr/local/bin/7z",
                "/data/data/com.termux/files/usr/bin/7z"
            ],
            "apktool": [
                r"C:\Android\JAR\apktool_3.0.3.jar",
                r"C:\Android\JAR\apktool.jar",
                "/usr/local/bin/apktool",
                "/usr/bin/apktool",
                "/data/data/com.termux/files/usr/bin/apktool"
            ],
            "zipalign": [
                r"C:\Android\build-tools\35.0.0\zipalign.exe",
                r"C:\Android\build-tools\34.0.0\zipalign.exe",
                r"C:\Android\build-tools\33.0.0\zipalign.exe",
                "/usr/bin/zipalign",
                "/usr/local/bin/zipalign",
                "/data/data/com.termux/files/usr/bin/zipalign"
            ] + [os.path.join(d, "zipalign.exe" if os.name == 'nt' else "zipalign") for d in sdk_candidates],
            "apksigner": [
                r"C:\Android\build-tools\35.0.0\apksigner.bat",
                r"C:\Android\build-tools\35.0.0\apksigner.jar",
                r"C:\Android\build-tools\34.0.0\apksigner.bat",
                r"C:\Android\build-tools\33.0.0\apksigner.bat",
                "/usr/bin/apksigner",
                "/usr/local/bin/apksigner",
                "/data/data/com.termux/files/usr/bin/apksigner"
            ] + [os.path.join(d, "apksigner.bat" if os.name == 'nt' else "apksigner") for d in sdk_candidates]
        }
        
        for candidate in common_locations.get(tool_name, []):
            if os.path.exists(candidate):
                return candidate
                
        path_tool = shutil.which(tool_name)
        if path_tool:
            return path_tool
            
        return None

    @classmethod
    def ensure_default_config_file(cls) -> None:
        """Generates a default config.txt template if not present."""
        cfg_path = cls.get_config_path()
        if not os.path.exists(cfg_path):
            apktool = cls.find_tool("apktool") or ""
            seven_zip = cls.find_tool("7z") or ""
            zipalign = cls.find_tool("zipalign") or ""
            apksigner = cls.find_tool("apksigner") or ""
            
            content = f"""# ==============================================================================
# WhatsApp Clone Tool - External Build Tools Configuration
# ==============================================================================
# Leave paths empty or commented out to automatically detect from Environment/PATH.

# Path to Apktool (.jar or executable script)
APKTOOL_PATH={apktool}

# Path to 7-Zip executable (7z.exe on Windows or 7z on Linux/Termux)
SEVEN_ZIP_PATH={seven_zip}

# Path to Android SDK zipalign executable
ZIPALIGN_PATH={zipalign}

# Path to Android SDK apksigner (.bat, .jar, or executable)
APKSIGNER_PATH={apksigner}

# Keystore configuration for signing cloned APKs
KEYSTORE_PATH=towartz.jks
KEYSTORE_PASS=pass:towartz123
KEYSTORE_ALIAS=towartz

# Default worker thread count for parallel Smali/XML processing
DEFAULT_WORKERS=12
"""
            try:
                with open(cfg_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception:
                pass


class ApkPackager:
    """1:1 Direct-Copy Exact ZIP Repack & APK Signing Engine"""

    @staticmethod
    def find_tool(tool_name: str) -> Optional[str]:
        return ToolConfig.find_tool(tool_name)

    @staticmethod
    def decompile_with_apktool(apk_path: str, output_folder: str, apktool_jar: Optional[str] = None) -> bool:
        """Decompile an APK using Apktool."""
        tool_path = apktool_jar or ApkPackager.find_tool("apktool")
        if not tool_path or not os.path.exists(tool_path):
            print(TerminalUI.colorize("  [!] Apktool not found. Please specify path in config.txt or CLI.", TerminalUI.RED))
            return False
            
        print(TerminalUI.colorize(f"  [+] Decompiling APK ({os.path.basename(apk_path)}) with Apktool...", TerminalUI.CYAN))
        if tool_path.lower().endswith(".jar"):
            cmd = ["java", "-jar", tool_path, "d", "-f", apk_path, "-o", output_folder]
        else:
            cmd = [tool_path, "d", "-f", apk_path, "-o", output_folder]

        try:
            p = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            if p.returncode != 0:
                print(TerminalUI.colorize(f"  [!] Apktool decompile failed:\n{p.stderr}", TerminalUI.RED))
                return False
            print(TerminalUI.colorize(f"  [✓] Decompiled successfully to: {os.path.basename(output_folder)}", TerminalUI.GREEN))
            return True
        except Exception as e:
            print(TerminalUI.colorize(f"  [!] Failed to execute Apktool: {e}", TerminalUI.RED))
            return False

    @staticmethod
    def build_with_apktool(decompiled_folder: str, output_unsigned: str, apktool_jar: Optional[str] = None) -> bool:
        """Recompile decompiled folder into unsigned APK using Apktool."""
        tool_path = apktool_jar or ApkPackager.find_tool("apktool")
        if not tool_path or not os.path.exists(tool_path):
            print(TerminalUI.colorize("  [!] Apktool not found. Please specify path in config.txt or CLI.", TerminalUI.RED))
            return False
            
        print(TerminalUI.colorize(f"  [+] Recompiling with Apktool: {os.path.basename(tool_path)}...", TerminalUI.CYAN))
        if tool_path.lower().endswith(".jar"):
            cmd = ["java", "-jar", tool_path, "b", decompiled_folder, "-o", output_unsigned]
        else:
            cmd = [tool_path, "b", decompiled_folder, "-o", output_unsigned]

        try:
            p = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            if p.returncode != 0:
                print(TerminalUI.colorize(f"  [!] Apktool build failed:\n{p.stderr}", TerminalUI.RED))
                return False
            print(TerminalUI.colorize("  [✓] Bytecode & Manifest compiled into unsigned APK.", TerminalUI.GREEN))
            return True
        except Exception as e:
            print(TerminalUI.colorize(f"  [!] Failed to execute Apktool: {e}", TerminalUI.RED))
            return False

    @staticmethod
    def repack_exact_copy(
        base_apk: str, 
        unsigned_apk: str, 
        output_apk: str, 
        sign: bool = False,
        keystore: Optional[str] = None, 
        keypass: Optional[str] = None, 
        keyalias: Optional[str] = None
    ) -> bool:
        """
        Direct 1:1 bitwise copy of base.apk, in-place removal of old signature blocks,
        in-place injection of updated DEX & manifest, 4-byte zipalign, and optional V1/V2/V3 signing.
        """
        keypass = keypass or ToolConfig.get("KEYSTORE_PASS", "pass:towartz123")
        keyalias = keyalias or ToolConfig.get("KEYSTORE_ALIAS", "towartz")
        
        try:
            seven_zip = ApkPackager.find_tool("7z")
            zipalign = ApkPackager.find_tool("zipalign")
            apksigner = ApkPackager.find_tool("apksigner")
            
            stage_dir = os.path.join(os.path.dirname(unsigned_apk) or ".", "stage_update")
            if os.path.exists(stage_dir):
                shutil.rmtree(stage_dir)
            os.makedirs(stage_dir, exist_ok=True)
            
            # Step 1: Extract updated DEX & AndroidManifest from unsigned APK
            update_files = []
            with zipfile.ZipFile(unsigned_apk, 'r') as zc:
                for name in zc.namelist():
                    if name == 'AndroidManifest.xml' or (name.startswith('classes') and name.endswith('.dex')):
                        zc.extract(name, stage_dir)
                        update_files.append(name)
            
            temp_copy = os.path.join(os.path.dirname(unsigned_apk) or ".", "temp_direct_copy.apk")
            if os.path.exists(temp_copy):
                os.remove(temp_copy)
            
            # Step 2: 1:1 direct bitwise copy of base.apk
            print(TerminalUI.colorize(f"  [1] 1:1 Copying base archive ({os.path.basename(base_apk)})...", TerminalUI.CYAN))
            shutil.copyfile(base_apk, temp_copy)
            
            if seven_zip:
                # Remove old signature blocks using 7z
                print(TerminalUI.colorize("  [2] Removing old signature files from copied APK...", TerminalUI.CYAN))
                cmd_del = [seven_zip, 'd', '-tzip', temp_copy, 'META-INF/*.SF', 'META-INF/*.RSA', 'META-INF/*.DSA', 'META-INF/*.EC', 'META-INF/MANIFEST.MF']
                subprocess.run(cmd_del, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # In-place inject updated DEX & AndroidManifest
                print(TerminalUI.colorize("  [3] In-place updating modified DEX and AndroidManifest into APK...", TerminalUI.CYAN))
                subprocess.run([seven_zip, 'a', '-tzip', temp_copy, '*'], cwd=stage_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            else:
                # Python fallback with metadata preservation
                print(TerminalUI.colorize("  [2] In-place updating modified DEX and AndroidManifest (Python engine)...", TerminalUI.CYAN))
                repack_unaligned = os.path.join(os.path.dirname(unsigned_apk) or ".", "temp_py_repack.apk")
                def is_sig(n):
                    u = n.upper()
                    return u.startswith('META-INF/') and (u.endswith('.SF') or u.endswith('.RSA') or u.endswith('.DSA') or u.endswith('.EC') or u == 'META-INF/MANIFEST.MF')
                
                with zipfile.ZipFile(unsigned_apk, 'r') as zc, zipfile.ZipFile(base_apk, 'r') as zb:
                    cloned_data = {n: zc.read(n) for n in update_files}
                    with zipfile.ZipFile(repack_unaligned, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
                        for item in zb.infolist():
                            if is_sig(item.filename):
                                continue
                            if item.filename in cloned_data:
                                zout.writestr(item, cloned_data[item.filename])
                            else:
                                zout.writestr(item, zb.read(item.filename))
                temp_copy = repack_unaligned
            
            shutil.rmtree(stage_dir, ignore_errors=True)
            
            # Step 3: Zipalign 4-byte
            temp_aligned = os.path.join(os.path.dirname(unsigned_apk) or ".", "temp_aligned.apk")
            target_aligned = temp_aligned if sign else output_apk
            
            if os.path.exists(target_aligned):
                os.remove(target_aligned)
                
            if zipalign:
                print(TerminalUI.colorize("  [4] Running 4-byte zipalign...", TerminalUI.CYAN))
                subprocess.run([zipalign, '-f', '-p', '4', temp_copy, target_aligned], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            else:
                shutil.copyfile(temp_copy, target_aligned)
            
            if os.path.exists(temp_copy):
                os.remove(temp_copy)
            
            # Step 4: Optional signing with apksigner (V1+V2+V3)
            if sign:
                if apksigner and keystore and os.path.exists(keystore):
                    print(TerminalUI.colorize("  [5] Signing with apksigner (V1, V2, V3)...", TerminalUI.CYAN))
                    if os.path.exists(output_apk):
                        os.remove(output_apk)
                    cmd_sign = [
                        apksigner, 'sign',
                        '--ks', keystore,
                        '--ks-pass', keypass,
                        '--ks-key-alias', keyalias,
                        '--key-pass', keypass,
                        '--out', output_apk,
                        temp_aligned
                    ]
                    subprocess.run(cmd_sign, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                    
                    if os.path.exists(temp_aligned):
                        os.remove(temp_aligned)
                    
                    # Verify
                    print(TerminalUI.colorize("  [6] Verifying final APK signature...", TerminalUI.CYAN))
                    subprocess.run([apksigner, 'verify', output_apk], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                    print(TerminalUI.colorize(f"\n[SUCCESS] Final signed APK ready at: {output_apk}", TerminalUI.BOLD + TerminalUI.GREEN))
                else:
                    print(TerminalUI.colorize("  [!] apksigner or keystore not found. Outputting aligned unsigned APK.", TerminalUI.YELLOW))
                    if os.path.exists(temp_aligned) and temp_aligned != output_apk:
                        shutil.move(temp_aligned, output_apk)
                    print(TerminalUI.colorize(f"\n[SUCCESS] Final unsigned cloned APK ready at: {output_apk}", TerminalUI.BOLD + TerminalUI.GREEN))
            else:
                print(TerminalUI.colorize(f"\n[SUCCESS] Final unsigned cloned APK (aligned & ready to sign) ready at: {output_apk}", TerminalUI.BOLD + TerminalUI.GREEN))
            
            return True
        except Exception as e:
            print(TerminalUI.colorize(f"  [!] Packaging failed: {e}", TerminalUI.RED))
            return False


class WhatsAppCloner:
    
    def __init__(self):
        ToolConfig.ensure_default_config_file()
        self.config = WhatsAppCloneConfig()
        self.build_apk = False
        self.sign_apk = False
        self.base_apk = None
        self.out_apk = None
        self.keystore = ToolConfig.get("KEYSTORE_PATH", "towartz.jks")
        self.keypass = ToolConfig.get("KEYSTORE_PASS", "pass:towartz123")
        self.keyalias = ToolConfig.get("KEYSTORE_ALIAS", "towartz")
        
        auto_sign_cfg = ToolConfig.get("AUTO_SIGN", "false").lower()
        self.sign_apk = (auto_sign_cfg in ("true", "1", "yes"))
        
        default_workers_str = ToolConfig.get("DEFAULT_WORKERS", "12")
        try:
            self.config.max_workers = int(default_workers_str)
        except ValueError:
            self.config.max_workers = 12
        
    def display_intro(self):
        title = "WhatsApp Clone Tool"
        subtitle = "v3.0.0 (Zero Dependencies)"
        lines = [
            TerminalUI.colorize("Universal APK clone utility for WhatsApp, WhatsApp Lite, Business & WAMODs.", TerminalUI.WHITE),
            "",
            TerminalUI.colorize("[+] Auto-detects base package from AndroidManifest.xml", TerminalUI.CYAN),
            TerminalUI.colorize("[+] Remaps all 11+ Content Provider authorities (Prevents Conflicting Provider)", TerminalUI.CYAN),
            TerminalUI.colorize("[+] Remaps all custom permissions & multi-DEX smali folders", TerminalUI.CYAN),
            TerminalUI.colorize("[+] 1:1 Direct-Copy Exact ZIP Repack Engine (Default: Unsigned)", TerminalUI.CYAN),
            TerminalUI.colorize("[+] Dynamic tool path auto-detection & config.txt support", TerminalUI.CYAN),
            "",
            TerminalUI.colorize("Author: YouTube@66XZD", TerminalUI.DIM)
        ]
        TerminalUI.print_panel(title, subtitle, lines, TerminalUI.CYAN)
        print()
    
    def parse_arguments(self) -> bool:
        parser = argparse.ArgumentParser(description="WhatsApp Clone Tool v3.0.0", add_help=False)
        parser.add_argument("folder", nargs="?", help="The root folder of decompiled code OR a .apk file")
        parser.add_argument(
            "--whatsapp-type", type=int, choices=[1, 2, 3], 
            help="WhatsApp type: 1 for WhatsApp, 2 for WhatsApp Business, 3 for Custom/Auto"
        )
        parser.add_argument(
            "--mode", type=int, choices=[1, 2, 3],
            help="Mode: 1 for Auto, 2 for Custom Base, 3 for Custom ALL"
        )
        parser.add_argument("--package", help="New package name without 'com.' prefix (e.g. 'mywa')")
        parser.add_argument("--name", help="New storage folder name (e.g. 'MyWhatsApp')")
        parser.add_argument("--search-pattern", help="Custom search pattern for base package (Mode 3 only)")
        parser.add_argument(
            "--workers", type=int, default=None,
            help=f"Number of worker threads for parallel processing (Default from config: {self.config.max_workers})"
        )
        parser.add_argument("--build", action="store_true", help="Automatically build & repack final cloned APK")
        parser.add_argument("--base-apk", help="Path to base.apk template for 1:1 direct-copy repack")
        parser.add_argument("--out-apk", help="Output path for final APK (Default: <package>_ExactZip_cloned.apk)")
        parser.add_argument("--sign", action="store_true", help="Sign the output APK with apksigner (Default: unsigned)")
        parser.add_argument("--keystore", help=f"Path to keystore .jks for signing (Default: {self.keystore})")
        parser.add_argument("--key-pass", help="Keystore password (default from config)")
        parser.add_argument("--key-alias", help="Keystore alias (default from config)")
        parser.add_argument("--clean", "--force-decompile", action="store_true", help="Force clean re-decompilation if decompiled folder already exists")
        parser.add_argument("-h", "--help", action="store_true", help="Show help message and exit")
        
        args = parser.parse_args()
        
        if args.help:
            show_help()
        
        if args.folder:
            target_path = os.path.abspath(args.folder)
            if os.path.isfile(target_path) and target_path.lower().endswith(".apk"):
                self.base_apk = target_path
                self.build_apk = True
                apk_stem = os.path.splitext(os.path.basename(target_path))[0]
                decompiled_dir = os.path.join(os.path.dirname(target_path), f"decompiled_{apk_stem}")
                self.config.root_folder = decompiled_dir
                
                if args.clean and os.path.exists(decompiled_dir):
                    shutil.rmtree(decompiled_dir, ignore_errors=True)
                    
                manifest_check = os.path.join(decompiled_dir, "AndroidManifest.xml")
                if not os.path.exists(manifest_check):
                    decompiled = ApkPackager.decompile_with_apktool(self.base_apk, decompiled_dir)
                    if not decompiled:
                        print(TerminalUI.colorize("  [!] Decompilation failed. Aborting.", TerminalUI.RED))
                        sys.exit(1)
                self.config.detect_from_manifest()
            else:
                self.config.root_folder = target_path
                self.config.detect_from_manifest()
        
        if args.workers:
            self.config.max_workers = args.workers
        if args.build:
            self.build_apk = True
        if args.sign:
            self.sign_apk = True
        if args.base_apk:
            self.base_apk = args.base_apk
        self.out_apk = args.out_apk
        
        if args.keystore:
            self.keystore = args.keystore
        elif not os.path.isabs(self.keystore) and self.config.root_folder:
            parent_ks = os.path.join(os.path.dirname(self.config.root_folder), self.keystore)
            if os.path.exists(parent_ks):
                self.keystore = parent_ks
                
        if args.key_pass:
            self.keypass = args.key_pass
        if args.key_alias:
            self.keyalias = args.key_alias
        
        if args.folder and args.mode:
            self.setup_from_args(args)
            return True
        else:
            return False
    
    def setup_from_args(self, args) -> None:
        if args.whatsapp_type == 1:
            self.config.detected_base_pkg = "com.whatsapp"
            self.config.current_folder_name = "WhatsApp"
            default_pkg = "universe.messenger"
        elif args.whatsapp_type == 2:
            self.config.detected_base_pkg = "com.whatsapp.w4b"
            self.config.current_folder_name = "WhatsApp Business"
            default_pkg = "universe.messenger"
        else:
            self.config.detect_from_manifest()
            default_pkg = "universe.messenger"
            
        if args.mode == 1:
            self.config.new_package_name = default_pkg
            self.config.new_folder_name = self.config.current_folder_name
        elif args.mode == 2:
            if not args.package or not args.name:
                print(TerminalUI.colorize("ERROR: --package and --name are required with --mode 2", TerminalUI.RED))
                sys.exit(1)
            self.config.new_package_name = args.package.removeprefix("com.")
            self.config.new_folder_name = args.name
        elif args.mode == 3:
            if not args.package or not args.name or not args.search_pattern:
                print(TerminalUI.colorize("ERROR: --package, --name, and --search-pattern are required with --mode 3", TerminalUI.RED))
                sys.exit(1)
            self.config.new_package_name = args.package.removeprefix("com.")
            self.config.new_folder_name = args.name
            self.config.custom_search_pattern = args.search_pattern
            
        self.config.new_package_name_path = self.config.new_package_name.replace(".", "/")
    
    def find_local_candidates(self) -> List[Tuple[str, str, str]]:
        """
        Scans current directory for candidate APK files and decompiled folders.
        Returns list of (absolute_path, type_label, info_str).
        """
        candidates = []
        cwd = os.getcwd()
        
        # 1. Look for APK files in current directory
        try:
            for f in sorted(os.listdir(cwd)):
                full_path = os.path.join(cwd, f)
                if os.path.isfile(full_path) and f.lower().endswith(".apk"):
                    f_lower = f.lower()
                    if any(tag in f_lower for tag in ("cloned", "unsigned", "unaligned", "aligned", "directcopy", "temp_")):
                        continue
                    size_mb = os.path.getsize(full_path) / (1024 * 1024)
                    candidates.append((full_path, "APK File", f"{size_mb:.1f} MB"))
        except Exception:
            pass
            
        # 2. Look for decompiled folders in current directory
        try:
            for d in sorted(os.listdir(cwd)):
                full_dir = os.path.join(cwd, d)
                if os.path.isdir(full_dir) and d not in ("build", ".cache", ".git", "dist", "stage_update", "__pycache__"):
                    manifest = os.path.join(full_dir, "AndroidManifest.xml")
                    if os.path.exists(manifest):
                        candidates.append((full_dir, "Decompiled Folder", "AndroidManifest.xml found"))
        except Exception:
            pass
            
        return candidates

    def setup_interactively(self) -> None:
        if not self.config.root_folder:
            candidates = self.find_local_candidates()
            selected_path = None
            
            if candidates:
                opts = [(os.path.basename(p), f"{k}, {inf}") for p, k, inf in candidates]
                opts.append(("Enter custom path manually", "Type custom folder or APK path"))
                sel = InteractiveMenu.select(
                    "Select Target APK or Decompiled Folder",
                    opts,
                    default_index=0
                )
                if sel < len(candidates):
                    selected_path = candidates[sel][0]
            
            if not selected_path:
                prompt_str = TerminalUI.colorize("Enter root folder path of decompiled APK or APK file", TerminalUI.CYAN)
                user_input = input(f"{prompt_str} (or Enter for current dir): ").strip() or os.getcwd()
                selected_path = os.path.abspath(user_input)
                
            target_path = os.path.abspath(selected_path)
            if os.path.isfile(target_path) and target_path.lower().endswith(".apk"):
                self.base_apk = target_path
                self.build_apk = True
                apk_stem = os.path.splitext(os.path.basename(target_path))[0]
                decompiled_dir = os.path.join(os.path.dirname(target_path), f"decompiled_{apk_stem}")
                self.config.root_folder = decompiled_dir
                
                manifest_check = os.path.join(decompiled_dir, "AndroidManifest.xml")
                if os.path.exists(manifest_check):
                    decompile_choice = InteractiveMenu.select(
                        f"Existing '{os.path.basename(decompiled_dir)}' Detected",
                        [
                            ("Clean Fresh Decompile (Recommended)", f"Remove old folder & decompile {os.path.basename(target_path)} cleanly"),
                            ("Reuse Existing Folder (Fast)", "Keep current files without re-decompiling")
                        ],
                        default_index=0
                    )
                    if decompile_choice == 0:
                        print(TerminalUI.colorize(f"  [*] Removing old '{os.path.basename(decompiled_dir)}' for fresh decompile...", TerminalUI.CYAN))
                        shutil.rmtree(decompiled_dir, ignore_errors=True)
                
                if not os.path.exists(decompiled_dir) or not os.path.exists(manifest_check):
                    decompiled = ApkPackager.decompile_with_apktool(self.base_apk, decompiled_dir)
                    if not decompiled:
                        print(TerminalUI.colorize("  [!] Decompilation failed. Aborting.", TerminalUI.RED))
                        sys.exit(1)
            else:
                self.config.root_folder = target_path
        
        self.config.root_folder = os.path.abspath(self.config.root_folder)
        detected_pkg, folder_name = self.config.detect_from_manifest()
        
        # WhatsApp Type / Base selection
        type_options = [
            (f"Auto-detected ({detected_pkg})", folder_name),
            ("Standard WhatsApp", "com.whatsapp (Folder: WhatsApp)"),
            ("WhatsApp Business", "com.whatsapp.w4b (Folder: WhatsApp Business)")
        ]
        sel_type = InteractiveMenu.select("Select WhatsApp Base Type", type_options, default_index=0)
        if sel_type == 1:
            self.config.detected_base_pkg = "com.whatsapp"
            self.config.current_folder_name = "WhatsApp"
        elif sel_type == 2:
            self.config.detected_base_pkg = "com.whatsapp.w4b"
            self.config.current_folder_name = "WhatsApp Business"
            
        # Operation Mode selection
        mode_options = [
            ("Auto", "Default clone package (com.universe.messenger)"),
            ("Custom Package", "Clone base to new custom package name (e.g. towartz.wa)"),
            ("Custom ALL", "Clone of Cloned base with custom search pattern")
        ]
        sel_mode = InteractiveMenu.select("Select Operation Mode", mode_options, default_index=1)
        mode = str(sel_mode + 1)
        default_pkg = "universe.messenger"
        
        if mode == "1":
            self.config.new_package_name = default_pkg
            self.config.new_folder_name = self.config.current_folder_name
        elif mode == "2":
            pkg_input = input(TerminalUI.colorize("\nEnter new package name without 'com.' prefix (e.g. 'towartz.wa') [default: 'towartz.wa']: ", TerminalUI.CYAN)).strip() or "towartz.wa"
            self.config.new_package_name = pkg_input.removeprefix("com.")
            self.config.new_folder_name = input(TerminalUI.colorize(f"Enter new storage folder name [default: '{self.config.current_folder_name}']: ", TerminalUI.CYAN)).strip() or self.config.current_folder_name
        else:
            pkg_input = input(TerminalUI.colorize("\nEnter new package name without 'com.' prefix [default: 'towartz.wa']: ", TerminalUI.CYAN)).strip() or "towartz.wa"
            self.config.new_package_name = pkg_input.removeprefix("com.")
            self.config.new_folder_name = input(TerminalUI.colorize(f"Enter new storage folder name [default: '{self.config.current_folder_name}']: ", TerminalUI.CYAN)).strip() or self.config.current_folder_name
            self.config.custom_search_pattern = input(TerminalUI.colorize(f"Enter custom search pattern to replace [default: '{self.config.detected_base_pkg}']: ", TerminalUI.CYAN)).strip() or self.config.detected_base_pkg
            
        self.config.new_package_name_path = self.config.new_package_name.replace(".", "/")
    
    def validate_config(self) -> bool:
        if not os.path.isdir(self.config.root_folder):
            print(TerminalUI.colorize(f"\nERROR: The specified directory does not exist: {self.config.root_folder}", TerminalUI.RED))
            return False
            
        if not self.config.new_package_name or not self.config.new_folder_name:
            print(TerminalUI.colorize("\nERROR: Package name and folder name cannot be empty.", TerminalUI.RED))
            return False
            
        return True
    
    def run(self) -> None:
        if not self.validate_config():
            return
            
        print()
        self.config.display_config()
        print()
        
        # Process SMALI
        print(TerminalUI.colorize("[*] Processing .smali files across all multi-DEX folders...", TerminalUI.BOLD + TerminalUI.BLUE))
        smali_processor = SmaliProcessor(self.config)
        total_smali, success_smali = smali_processor.process_all_files()
        
        # Process XML
        print(TerminalUI.colorize("\n[*] Processing .xml files (AndroidManifest, Providers, Permissions, Filepaths)...", TerminalUI.BOLD + TerminalUI.BLUE))
        xml_processor = XmlProcessor(self.config)
        total_xml, success_xml = xml_processor.process_all_files()
        
        # Summary
        print()
        headers = ["File Type", "Total Files", "Processed", "Success Rate"]
        smali_rate = f"{(success_smali/total_smali)*100:.1f}%" if total_smali > 0 else "N/A"
        xml_rate = f"{(success_xml/total_xml)*100:.1f}%" if total_xml > 0 else "N/A"
        
        rows = [
            ["SMALI Bytecode", str(total_smali), str(success_smali), TerminalUI.colorize(smali_rate, TerminalUI.GREEN)],
            ["XML Resources", str(total_xml), str(success_xml), TerminalUI.colorize(xml_rate, TerminalUI.GREEN)]
        ]
        TerminalUI.print_table("Operation Summary", headers, rows)
        success_icon = "[✓]" if TerminalUI.supports_unicode() else "[OK]"
        print(TerminalUI.colorize(f"\n{success_icon} WhatsApp cloning completed successfully!\n", TerminalUI.BOLD + TerminalUI.GREEN))
        
        # Check automatic build/repack
        base_dir = os.path.dirname(self.config.root_folder) or "."
        default_base_apk = os.path.join(base_dir, "base.apk")
        
        should_build = self.build_apk
        if not should_build and sys.stdin.isatty():
            should_build = InteractiveMenu.confirm(
                "Build & package 1:1 exact ZIP cloned APK now?",
                default=True
            )
            
        if should_build:
            base_apk_path = self.base_apk or default_base_apk
            if not os.path.exists(base_apk_path):
                if sys.stdin.isatty():
                    base_apk_path = input(f"Enter path to original base.apk [{default_base_apk}]: ").strip() or default_base_apk
            
            if not os.path.exists(base_apk_path):
                print(TerminalUI.colorize(f"  [!] base.apk not found at: {base_apk_path}. Skipping APK packaging.", TerminalUI.YELLOW))
                return
                
            out_unsigned = os.path.join(base_dir, f"{self.config.new_package_name}_unsigned.apk")
            out_apk = self.out_apk or os.path.join(base_dir, f"{self.config.new_package_name}_ExactZip_cloned.apk")
            
            print(TerminalUI.colorize("\n[*] Starting 1:1 Direct-Copy Exact ZIP Packaging Pipeline...", TerminalUI.BOLD + TerminalUI.CYAN))
            built = ApkPackager.build_with_apktool(self.config.root_folder, out_unsigned)
            if built:
                ApkPackager.repack_exact_copy(
                    base_apk=base_apk_path,
                    unsigned_apk=out_unsigned,
                    output_apk=out_apk,
                    sign=self.sign_apk,
                    keystore=self.keystore,
                    keypass=self.keypass,
                    keyalias=self.keyalias
                )


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ["-help", "--help", "-h"]:
        show_help()
    
    try:
        cloner = WhatsAppCloner()
        cloner.display_intro()
        
        has_args = cloner.parse_arguments()
        if not has_args:
            cloner.setup_interactively()
            
        cloner.run()
        
    except KeyboardInterrupt:
        print(TerminalUI.colorize("\n\n[!] Process interrupted by user.", TerminalUI.YELLOW))
        sys.exit(1)
    except Exception as e:
        print(TerminalUI.colorize(f"\n[!] An unexpected error occurred: {e}", TerminalUI.RED))
        sys.exit(1)


if __name__ == "__main__":
    main()
