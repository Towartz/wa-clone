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


def render_progress_bar(task_name: str, current: int, total: int, start_time: float, bar_width: int = 25) -> None:
    """Renders a dynamic real-time progress bar with ETA and rate."""
    if total <= 0:
        return
    use_unicode = TerminalUI.supports_unicode()
    fill_char = "█" if use_unicode else "#"
    empty_char = "░" if use_unicode else "-"

    percent = (current / total) * 100.0
    filled = int(bar_width * current // total)
    bar = fill_char * filled + empty_char * (bar_width - filled)
    
    elapsed = time.time() - start_time
    rate = current / elapsed if elapsed > 0 else 0
    eta = (total - current) / rate if rate > 0 else 0
    
    elapsed_str = time.strftime("%M:%S", time.gmtime(elapsed))
    eta_str = time.strftime("%M:%S", time.gmtime(eta))
    
    msg = f"\r  {TerminalUI.colorize(task_name, TerminalUI.CYAN)} [{TerminalUI.colorize(bar, TerminalUI.GREEN)}] {percent:5.1f}% ({current}/{total}) [{elapsed_str}<{eta_str}, {rate:.1f}it/s]"
    sys.stdout.write(msg)
    sys.stdout.flush()
    if current >= total:
        sys.stdout.write("\n")
        sys.stdout.flush()


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
    python whatsapp_clone.py [folder_path] [options]
    python whatsapp_clone.py -h/--help

ARGUMENTS:
    folder                The root folder of the decompiled WhatsApp APK
                          If not provided, you'll be prompted to enter it

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
                          (Default: 8)

    -h, --help            Display this help message

EXAMPLES:
    # Auto-detect base and clone with custom package name
    python whatsapp_clone.py ./decompiled_apk --mode 2 --package mywa --name MyWA

    # Process WhatsApp Business
    python whatsapp_clone.py ./decompiled_w4b --whatsapp-type 2 --mode 1

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
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            for idx, result in enumerate(executor.map(self.process_file, files), 1):
                if result:
                    success_count += 1
                if idx % 10 == 0 or idx == total_files:
                    render_progress_bar(self.__class__.__name__, idx, total_files, start_time)
                    
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
            
            # Step 3: Revert official Meta/WhatsApp internal modules back to official namespaces
            if "Business" in self.config.current_folder_name:
                content = self.official_dot_pattern.sub(r'\1whatsapp.w4b\2\3', content)
                content = self.official_slash_pattern.sub(r'\1whatsapp/w4b\2\3', content)
            else:
                content = self.official_dot_pattern.sub(r'\1whatsapp\2\3', content)
                content = self.official_slash_pattern.sub(r'\1whatsapp\2\3', content)
            
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
            
            # Step 3: Preserve official external package queries in <queries>
            content = re.sub(
                r'(<package\s+android:name=")' + re.escape(self.new_pkg) + r'(\.w4b"/>)',
                r'\1com.whatsapp\2',
                content
            )
            
            # Step 4: Remap Storage Folders (e.g. filepaths.xml)
            content = self.folder_pattern.sub(self.config.new_folder_name, content)
            
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
                
            return True
                
        except Exception:
            return False


class WhatsAppCloner:
    
    def __init__(self):
        self.config = WhatsAppCloneConfig()
        
    def display_intro(self):
        title = "WhatsApp Clone Tool"
        subtitle = "v3.0.0 (Zero Dependencies)"
        lines = [
            TerminalUI.colorize("Universal APK clone utility for WhatsApp, WhatsApp Lite, Business & WAMODs.", TerminalUI.WHITE),
            "",
            TerminalUI.colorize("[+] Auto-detects base package from AndroidManifest.xml", TerminalUI.CYAN),
            TerminalUI.colorize("[+] Remaps all 11+ Content Provider authorities (Prevents Conflicting Provider)", TerminalUI.CYAN),
            TerminalUI.colorize("[+] Remaps all custom permissions & multi-DEX smali folders", TerminalUI.CYAN),
            "",
            TerminalUI.colorize("Author: YouTube@66XZD", TerminalUI.DIM)
        ]
        TerminalUI.print_panel(title, subtitle, lines, TerminalUI.CYAN)
        print()
    
    def parse_arguments(self) -> bool:
        parser = argparse.ArgumentParser(description="WhatsApp Clone Tool v3.0.0", add_help=False)
        parser.add_argument("folder", nargs="?", help="The root folder of the decompiled WhatsApp code")
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
            "--workers", type=int, default=8,
            help="Number of worker threads for parallel processing (Default: 8)"
        )
        parser.add_argument("-h", "--help", action="store_true", help="Show help message and exit")
        
        args = parser.parse_args()
        
        if args.help:
            show_help()
        
        if args.folder:
            self.config.root_folder = os.path.abspath(args.folder)
            self.config.detect_from_manifest()
        
        self.config.max_workers = args.workers or 8
        
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
    
    def setup_interactively(self) -> None:
        if not self.config.root_folder:
            prompt_str = TerminalUI.colorize("Enter root folder path of decompiled APK", TerminalUI.CYAN)
            self.config.root_folder = input(f"{prompt_str} (or Enter for current dir): ").strip() or os.getcwd()
        
        self.config.root_folder = os.path.abspath(self.config.root_folder)
        detected_pkg, folder_name = self.config.detect_from_manifest()
        
        check_icon = "[+]" if TerminalUI.supports_unicode() else "[+]"
        print(f"\n{TerminalUI.colorize(check_icon, TerminalUI.GREEN)} Detected Base Package: {TerminalUI.colorize(detected_pkg, TerminalUI.BOLD + TerminalUI.CYAN)} ({folder_name})")
        print("\nSelect WhatsApp Type / Base:")
        print(f"  {TerminalUI.colorize('1.', TerminalUI.YELLOW)} Auto-detected ({detected_pkg})")
        print(f"  {TerminalUI.colorize('2.', TerminalUI.YELLOW)} Standard WhatsApp (com.whatsapp)")
        print(f"  {TerminalUI.colorize('3.', TerminalUI.YELLOW)} WhatsApp Business (com.whatsapp.w4b)")
        
        selection = input("\nEnter number (1, 2, or 3) [default: 1]: ").strip() or "1"
        if selection == "2":
            self.config.detected_base_pkg = "com.whatsapp"
            self.config.current_folder_name = "WhatsApp"
        elif selection == "3":
            self.config.detected_base_pkg = "com.whatsapp.w4b"
            self.config.current_folder_name = "WhatsApp Business"
            
        print("\nSelect Operation Mode:")
        print(f"  {TerminalUI.colorize('1.', TerminalUI.YELLOW)} Auto (com.universe.messenger)")
        print(f"  {TerminalUI.colorize('2.', TerminalUI.YELLOW)} Custom Package (Clone original base to new name)")
        print(f"  {TerminalUI.colorize('3.', TerminalUI.YELLOW)} Custom ALL (Clone of Cloned base with custom search)")
        
        mode = input("\nEnter mode number (1, 2, or 3) [default: 2]: ").strip() or "2"
        default_pkg = "universe.messenger"
        
        if mode == "1":
            self.config.new_package_name = default_pkg
            self.config.new_folder_name = self.config.current_folder_name
        elif mode == "2":
            pkg_input = input("\nEnter new package name without 'com.' prefix (e.g. 'towartz.wa') [default: 'towartz.wa']: ").strip() or "towartz.wa"
            self.config.new_package_name = pkg_input.removeprefix("com.")
            self.config.new_folder_name = input(f"Enter new storage folder name [default: '{self.config.current_folder_name}']: ").strip() or self.config.current_folder_name
        else:
            pkg_input = input("\nEnter new package name without 'com.' prefix [default: 'towartz.wa']: ").strip() or "towartz.wa"
            self.config.new_package_name = pkg_input.removeprefix("com.")
            self.config.new_folder_name = input(f"Enter new storage folder name [default: '{self.config.current_folder_name}']: ").strip() or self.config.current_folder_name
            self.config.custom_search_pattern = input(f"Enter custom search pattern to replace [default: '{self.config.detected_base_pkg}']: ").strip() or self.config.detected_base_pkg
            
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
        print(TerminalUI.colorize(f"\n{success_icon} WhatsApp cloning completed successfully! Ready for compilation.\n", TerminalUI.BOLD + TerminalUI.GREEN))


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
