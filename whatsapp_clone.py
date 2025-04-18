#!/usr/bin/env python3
"""
WhatsApp Clone Tool

This script allows cloning WhatsApp or WhatsApp Business applications
by modifying package names and resources in .smali and .xml files.

Usage:
    python whatsapp_clone.py [folder_path] [options]
    python whatsapp_clone.py -h/--help

Author: Python by YouTube@66XZD (デキ)
Note : Ported from .bat and .ps1 script (not my own)
Version: 2.2.0
"""

import os
import sys
import re
import glob
import time
import logging
import argparse
from typing import Pattern, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.layout import Layout
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

if RICH_AVAILABLE:
    console = Console()

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

OFFICIAL_MODULES = (
    "aborthooks|adscreation|anr|audioRecording|breakpad|calling|fieldstats|filter|"
    "infra|jid|media|messagetranslation|nativelibloader|protocol|pytorch|stickers|"
    "superpack|unity|util|voipcalling|wamsys|executorch|gwpasan|"
    "voicetranscription|AppShell|GifHelper|Mp4Ops|NativeMediaHandler|SmbAppShell|"
    "SqliteShell|StickyHeadersRecyclerView|VideoFrameConverter|ohai|WaOhaiClient|productinfra|music|api|MusicApi" # add Fix Music status
)

def show_help():
    help_text = """
WhatsApp Clone Tool Help Guide
==============================

DESCRIPTION:
    This tool allows you to create modified clones of WhatsApp or WhatsApp Business
    applications by modifying package names and resources in decompiled APK files.

USAGE:
    python whatsapp_clone.py [folder_path] [options]
    python whatsapp_clone.py -h/--help

ARGUMENTS:
    folder                The root folder of the decompiled WhatsApp code
                          If not provided, you'll be prompted to enter it

OPTIONS:
    --whatsapp-type INT   Specify WhatsApp type:
                          1 = WhatsApp
                          2 = WhatsApp Business

    --mode INT            Select operation mode:
                          1 = Auto (uses default package names)
                          2 = Custom (lets you specify custom package names)
                          3 = Custom ALL (fully customize including search patterns)

    --package STRING      New package name without 'com'
                          (Required with --mode 2 or 3)

    --name STRING         New folder name
                          (Required with --mode 2 or 3)
                          
    --search-pattern STRING  Custom search pattern for package
                          (Only with --mode 3)

    --workers INT         Number of worker threads for parallel processing
                          (Default: 4)

    -h, --help            Display this help message

EXAMPLES:
    # Process with fully custom settings including search pattern
    python whatsapp_clone.py /path/to/decompiled --whatsapp-type 1 --mode 3 --package mywhatsapp --name MyWhatsApp --search-pattern "com.whatsapp"

    # Run interactively (will prompt for all options)
    python whatsapp_clone.py

    # Process WhatsApp in the current directory with default settings
    python whatsapp_clone.py . --whatsapp-type 1 --mode 1

    # Process WhatsApp with custom package name
    python whatsapp_clone.py /path/to/decompiled --whatsapp-type 1 --mode 2 --package mywhatsapp --name MyWhatsApp

    # Process WhatsApp Business with 8 worker threads
    python whatsapp_clone.py /path/to/decompiled --whatsapp-type 2 --mode 1 --workers 8

NOTES:
    - The tool requires a decompiled WhatsApp APK. You can use a tool like apktool to decompile the APK.
    - The tool modifies .smali and .xml files to change package names and references.
    - After running this tool, you'll need to recompile the APK using apktool.
    - Make sure to sign the APK after recompilation.

AUTHOR:
    YouTube@66XZD (デキ)
    Note: Ported from .bat and .ps1 script (not my own)
"""
    if RICH_AVAILABLE:
        help_panel = Panel(
            help_text, 
            title="[bold cyan]WhatsApp Clone Tool Help[/bold cyan]",
            border_style="blue",
            expand=False
        )
        console.print(help_panel)
    else:
        print(help_text)
    sys.exit(0)

class WhatsAppCloneConfig:
    
    def __init__(self):
        self.root_folder: str = ""
        self.current_folder_name: str = ""
        self.new_package_name: str = ""
        self.new_folder_name: str = ""
        self.new_package_name_path: str = ""
        self.custom_search_pattern: str = ""
        self.max_workers: int = 8  
        
    def get_config_table(self) -> Table:
        table = Table(show_header=False, box=box.ROUNDED)
        table.add_column("Parameter", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Root folder", self.root_folder)
        table.add_row("Current folder name", self.current_folder_name)
        table.add_row("New package name", self.new_package_name)
        table.add_row("New folder name", self.new_folder_name)
        table.add_row("Package path format", self.new_package_name_path)
        if self.custom_search_pattern:
            table.add_row("Custom search pattern", self.custom_search_pattern)
        return table
        
    def __str__(self) -> str:
        if RICH_AVAILABLE:
            with console.capture() as capture:
                console.print(self.get_config_table())
            return capture.get()
        else:
            return (
                f"Root folder: {self.root_folder}\n"
                f"Current folder name: {self.current_folder_name}\n"
                f"New package name: {self.new_package_name}\n"
                f"New folder name: {self.new_folder_name}\n"
                f"Package path format: {self.new_package_name_path}"
            )


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
            if RICH_AVAILABLE:
                console.print(f"No [blue]{self.__class__.__name__}[/blue] files found to process.")
            else:
                logger.info(f"No {self.__class__.__name__} files found to process.")
            return 0, 0
        
        total_files = len(files)
        success_count = 0
        
        if RICH_AVAILABLE:
            with Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(complete_style="green"),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                task = progress.add_task(f"Processing {self.__class__.__name__} files", total=total_files)
                
                with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                    results = []
                    for result in executor.map(self.process_file, files):
                        results.append(result)
                        progress.update(task, advance=1)
                    
                success_count = sum(1 for result in results if result)
        else:
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                results = list(tqdm(
                    executor.map(self.process_file, files),
                    total=total_files,
                    desc=f"Processing {self.__class__.__name__} files"
                ))
                
            success_count = sum(1 for result in results if result)
            
        return total_files, success_count


class SmaliProcessor(FileProcessor):
    
    def __init__(self, config: WhatsAppCloneConfig):
        super().__init__(config)
        
        # Default patterns for regular WhatsApp
        self.package_pattern1 = re.compile(r'com(/)whatsapp')
        self.package_pattern2 = re.compile(r'com(\.)whatsapp')
        
        # Different patterns for WhatsApp Business to properly handle both
        # WhatsApp and WhatsApp Business patterns
        if hasattr(self.config, 'custom_search_pattern') and self.config.custom_search_pattern:
            # Create patterns from the custom search pattern
            custom_pattern = re.escape(self.config.custom_search_pattern)
            # Replace dots with regex to match either dots or slashes
            custom_pattern_slash = custom_pattern.replace('\\.', '(/)')
            custom_pattern_dot = custom_pattern.replace('\\.', '(\\.)')
            
            self.package_pattern1 = re.compile(custom_pattern_slash)
            self.package_pattern2 = re.compile(custom_pattern_dot)
        else:
            # Default patterns for regular WhatsApp
            self.package_pattern1 = re.compile(r'com(/)whatsapp')
            self.package_pattern2 = re.compile(r'com(\.)whatsapp')
            
            # Different patterns for WhatsApp Business to properly handle both
            # WhatsApp and WhatsApp Business patterns
            if "Business" in self.config.current_folder_name:
                self.package_pattern1 = re.compile(r'com(/)whatsapp(/w4b)?')
                self.package_pattern2 = re.compile(r'com(\.)whatsapp(\.w4b)?')
        
        self.official_package_pattern = re.compile(
            r'(\.)' + re.escape(self.config.new_package_name) + r'(\.)(' + OFFICIAL_MODULES + r')'
        )
        self.official_packageP_pattern = re.compile(
            r'(\.|/)' + re.escape(self.config.new_package_name_path) + r'(\.|/)(' + OFFICIAL_MODULES + r')'
        )
    
    def get_files(self) -> List[str]:
        return glob.glob(os.path.join(self.config.root_folder, "**", "*.smali"), recursive=True)
        
    def process_file(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            
            # Handle replacements differently for WhatsApp Business
            if "Business" in self.config.current_folder_name:
                # Preserve WhatsApp module references but replace WhatsApp Business references
                # First pass: handle explicit w4b paths
                explicit_w4b_pattern1 = re.compile(r'com(/)whatsapp(/w4b)')
                explicit_w4b_pattern2 = re.compile(r'com(\.)whatsapp(\.w4b)')
                
                content = explicit_w4b_pattern1.sub(f'com\\1{self.config.new_package_name_path}', content)
                content = explicit_w4b_pattern2.sub(f'com\\1{self.config.new_package_name}', content)
                
                # Second pass: handle core WhatsApp paths that aren't w4b
                # but make sure not to replace WhatsApp paths that were already handled
                core_wa_pattern1 = re.compile(r'com(/)whatsapp(?!/w4b)')
                core_wa_pattern2 = re.compile(r'com(\.)whatsapp(?!\.w4b)')
                
                content = core_wa_pattern1.sub(f'com\\1whatsapp', content)
                content = core_wa_pattern2.sub(f'com\\1whatsapp', content)
            else:
                # For regular WhatsApp, just replace all references
                content = self.package_pattern1.sub(f'com\\1{self.config.new_package_name_path}', content)
                content = self.package_pattern2.sub(f'com\\1{self.config.new_package_name}', content)
            
            # Handle official modules in both cases
            if "Business" in self.config.current_folder_name:
                content = self.official_package_pattern.sub(r'\1whatsapp.w4b\2\3', content)
                content = self.official_packageP_pattern.sub(r'\1whatsapp/w4b\2\3', content)
            else:
                content = self.official_package_pattern.sub(r'\1whatsapp\2\3', content)
                content = self.official_packageP_pattern.sub(r'\1whatsapp\2\3', content)
            
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            return True
                
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[bold red]Error processing {file_path}: {e}[/bold red]")
            else:
                logger.error(f"Error processing {file_path}: {e}")
            return False

class XmlProcessor(FileProcessor):
    
    def __init__(self, config: WhatsAppCloneConfig):
        super().__init__(config)
        
        if hasattr(self.config, 'custom_search_pattern') and self.config.custom_search_pattern:
            # Use custom search pattern
            self.package_pattern = re.compile(re.escape(self.config.custom_search_pattern))
            self.sticker_pattern = re.compile(r'android:name="' + re.escape(self.config.custom_search_pattern) + r'\.sticker\.READ"')
        else:
            if "Business" in self.config.current_folder_name:
                self.package_pattern = re.compile(r'com\.whatsapp(\.w4b)?')
                self.sticker_pattern = re.compile(r'android:name="com\.whatsapp(\.w4b)?\.sticker\.READ"')
            else:
                self.package_pattern = re.compile(r'com\.whatsapp')
                self.sticker_pattern = re.compile(r'android:name="com\.whatsapp\.sticker\.READ"')
        
        # Add the missing patterns
        self.folder_pattern = re.compile(re.escape(self.config.current_folder_name))
        
        # Add the official_package_pattern similar to SmaliProcessor
        self.official_package_pattern = re.compile(
            r'(\.)' + re.escape(self.config.new_package_name) + r'(\.)(' + OFFICIAL_MODULES + r')'
        )
        
    def get_files(self) -> List[str]:
        return glob.glob(os.path.join(self.config.root_folder, "**", "*.xml"), recursive=True)
        
    def process_file(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            
            content = self.package_pattern.sub(f'com.{self.config.new_package_name}', content)
            content = self.sticker_pattern.sub(
                f'android:name="com.{self.config.new_package_name}.sticker.READ"', content
            )
            content = self.folder_pattern.sub(self.config.new_folder_name, content)
            
            if "Business" in self.config.current_folder_name:
                content = self.official_package_pattern.sub(r'\1whatsapp.w4b\2\3', content)
            else:
                content = self.official_package_pattern.sub(r'\1whatsapp\2\3', content)
            
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
                
            return True
                
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[bold red]Error processing {file_path}: {e}[/bold red]")
            else:
                logger.error(f"Error processing {file_path}: {e}")
            return False


class WhatsAppCloner:
    
    def __init__(self):
        self.config = WhatsAppCloneConfig()
        
    def display_intro(self):
        if RICH_AVAILABLE:
            title = Text("WhatsApp Clone Tool", style="bold cyan")
            subtitle = Text("Script Version : v2.2.0", style="italic green")
            
            description = Text("\nThis tool allows you to create modified clones of WhatsApp by customizing package names and resources xml.")
            author = Text("\nAuthor: YouTube@66XZD (デキ)", style="blue")
            note = Text("Note: Ported from .bat and .ps1 script (not my own)", style="yellow")
            
            console.print(Panel(
                Text.assemble(title, "\n", subtitle, description, "\n", author, "\n", note),
                border_style="cyan",
                title="[bold white]WhatsApp Clone Tool[/bold white]",
                subtitle="[white]v2.2.0[/white]"
            ))
        else:
            print("\n=== WhatsApp Clone Tool - v2.2.0 ===")
            print("\nThis tool allows you to create modified clones of WhatsApp by customizing package names and resources xml.")
            print("\nAuthor: YouTube@66XZD (デキ)")
            print("Note: Ported from .bat and .ps1 script (not my own)")
            print("=" * 60 + "\n")
    
    def parse_arguments(self) -> None:
        parser = argparse.ArgumentParser(description="WhatsApp Clone Tool", add_help=False)
        parser.add_argument("folder", nargs="?", help="The root folder of the decompiled WhatsApp code")
        parser.add_argument(
            "--whatsapp-type", type=int, choices=[1, 2, 3], 
            help="WhatsApp type: 1 for WhatsApp, 2 for WhatsApp Business"
        )
        parser.add_argument(
            "--mode", type=int, choices=[1, 2, 3],
            help="Mode: 1 for Auto, 2 for Custom, 3 for Custom ALL"
        )
        parser.add_argument("--package", help="New package name without 'com'")
        parser.add_argument("--name", help="New folder name")
        parser.add_argument("--search-pattern", help="Custom search pattern for package (Mode 3 only)")
        parser.add_argument(
            "--workers", type=int, default=4,
            help="Number of worker threads for parallel processing"
        )
        parser.add_argument("-h", "--help", action="store_true", help="Show help message and exit")
        
        args = parser.parse_args()
        
        if args.help:
            show_help()
        
        if args.folder:
            self.config.root_folder = args.folder
        
        self.config.max_workers = args.workers or 4
        
        if args.folder and args.whatsapp_type and args.mode:
            self.setup_from_args(args)
            return True
        else:
            return False
    
    def setup_from_args(self, args) -> None:
        if args.whatsapp_type == 1:
            self.config.current_folder_name = "WhatsApp"
            default_pkg = "whatsapp"
        else:
            self.config.current_folder_name = "WhatsApp Business"
            default_pkg = "whatsapp.w4b"
            
        if args.mode == 1:
            self.config.new_package_name = default_pkg
            self.config.new_folder_name = "WhatsApp" if args.whatsapp_type == 1 else "WhatsApp Business"
        elif args.mode == 2:
            if not args.package or not args.name:
                if RICH_AVAILABLE:
                    console.print("[bold red]ERROR: --package and --name are required with --mode 2[/bold red]")
                else:
                    logger.error("--package and --name are required with --mode 2")
                sys.exit(1)
            self.config.new_package_name = args.package
            self.config.new_folder_name = args.name
        elif args.mode == 3:
            if not args.package or not args.name or not args.search_pattern:
                if RICH_AVAILABLE:
                    console.print("[bold red]ERROR: --package, --name, and --search-pattern are required with --mode 3[/bold red]")
                else:
                    logger.error("--package, --name, and --search-pattern are required with --mode 3")
                sys.exit(1)
            self.config.new_package_name = args.package
            self.config.new_folder_name = args.name
            self.config.custom_search_pattern = args.search_pattern
            
        self.config.new_package_name_path = self.config.new_package_name.replace(".", "/")
    
    def setup_interactively(self) -> None:
        if not self.config.root_folder:
            if RICH_AVAILABLE:
                self.config.root_folder = Prompt.ask(
                    "[bold cyan]Enter the root folder path[/bold cyan]",
                    default=os.getcwd()
                )
            else:
                self.config.root_folder = input("Enter the root folder path (or press Enter for current directory): ") or os.getcwd()
        
        if RICH_AVAILABLE:
            console.print("\n[bold magenta]Select which WhatsApp you want to clone:[/bold magenta]")
            console.print("[blue]1. [green]WhatsApp[/green][/blue]")
            console.print("[blue]2. [green]WhatsApp Business[/green][/blue]")
            
            selection = Prompt.ask(
                "[yellow]Enter the number[/yellow]",
                choices=["1", "2"],
                default="1"
            )
        else:
            print("\nSelect which WhatsApp you want to clone:")
            print("1. WhatsApp")
            print("2. WhatsApp Business")
            
            while True:
                selection = input("\nEnter the number (1 or 2): ")
                if selection in ["1", "2"]:
                    break
                else:
                    print("Invalid selection. Please try again.")
        
        if selection == "1":
            self.config.current_folder_name = "WhatsApp"
            default_pkg = "universe.messenger"
        else:
            self.config.current_folder_name = "WhatsApp Business"
            default_pkg = "universe.messenger"
        
        if RICH_AVAILABLE:
            console.print("\n[bold magenta]Mode?[/bold magenta]")
            console.print("[blue]1. [green]Auto - Automatically uses the default configuration.[/green][/blue]")
            console.print("[blue]2. [green]Custom WhatsApp Base - Clone the WhatsApp original base to Clone.[/green][/blue]")
            console.print("[blue]3. [green]Custom ALL (Clone base of Cloned) - Fully customizable, Can Clone of Cloned Base[/green][/blue]")
            
            mode = Prompt.ask(
                "[yellow]Type number[/yellow]",
                choices=["1", "2", "3"],
                default="1"
            )
        else:
            print("\nSelect Mode:")
            print("1. Auto - Automatically uses the default configuration.")
            print("2. Custom WhatsApp Base - Clone the WhatsApp base to Clone.")
            print("3. Custom ALL (Clone base of Cloned) - Fully customizable, Can Clone of Cloned Base")
            
            while True:
                mode = input("\nType number (1, 2, or 3): ")
                if mode in ["1", "2", "3"]:
                    break
                else:
                    print("Invalid selection. Please try again.")
        
        if mode == "1":
            self.config.new_package_name = default_pkg
            self.config.new_folder_name = self.config.current_folder_name
        elif mode == "2":
            if RICH_AVAILABLE:
                self.config.new_package_name = Prompt.ask(
                    "[yellow]Enter the new package name without the 'com'[/yellow]",
                    default=default_pkg
                )
                self.config.new_folder_name = Prompt.ask(
                    "[yellow]Enter the new folder name[/yellow]",
                    default=self.config.current_folder_name
                )
            else:
                self.config.new_package_name = input(f"Enter the new package name without the 'com': ") or default_pkg
                self.config.new_folder_name = input(f"Enter the new folder name: ") or self.config.current_folder_name
        else:  # mode == "3"
            if RICH_AVAILABLE:
                self.config.new_package_name = Prompt.ask(
                    "[yellow]Enter the new package name without the 'com'[/yellow]",
                    default=default_pkg
                )
                self.config.new_folder_name = Prompt.ask(
                    "[yellow]Enter the new folder name[/yellow]",
                    default=self.config.current_folder_name
                )
                default_search = "com.universe.messenger" if self.config.current_folder_name == "WhatsApp" else "com.gbwhatsapp"
                self.config.custom_search_pattern = Prompt.ask(
                    "[yellow]Enter the custom search pattern (e.g. com.universe.messenger)[/yellow]",
                    default=default_search
                )
            else:
                self.config.new_package_name = input(f"Enter the new package name without the 'com': ") or default_pkg
                self.config.new_folder_name = input(f"Enter the new folder name: ") or self.config.current_folder_name
                default_search = "com.whatsapp" if self.config.current_folder_name == "WhatsApp" else "com.whatsapp.w4b"
                self.config.custom_search_pattern = input(f"Enter the custom search pattern (default: {default_search}): ") or default_search
                    
        self.config.new_package_name_path = self.config.new_package_name.replace(".", "/")
    
    def validate_config(self) -> bool:
        if not os.path.isdir(self.config.root_folder):
            if RICH_AVAILABLE:
                console.print(f"[bold red]ERROR: The specified folder does not exist: {self.config.root_folder}[/bold red]")
            else:
                logger.error(f"The specified folder does not exist: {self.config.root_folder}")
            return False
            
        if not self.config.new_package_name or not self.config.new_folder_name:
            if RICH_AVAILABLE:
                console.print("[bold red]ERROR: Package name and folder name cannot be empty[/bold red]")
            else:
                logger.error("Package name and folder name cannot be empty")
            return False
            
        return True
    
    def run(self) -> None:
        if RICH_AVAILABLE:
            console.print("[bold magenta]Starting WhatsApp Clone Tool[/bold magenta]")
            console.print("[bold]Configuration:[/bold]")
            console.print(self.config.get_config_table())
        else:
            logger.info("Starting WhatsApp Clone Tool")
            logger.info(f"Configuration:\n{self.config}")
        
        if not self.validate_config():
            return
        
        if RICH_AVAILABLE:
            console.print("[bold blue]Processing .smali files[/bold blue]")
        else:
            logger.info("Processing .smali files")
            
        smali_processor = SmaliProcessor(self.config)
        total_smali, success_smali = smali_processor.process_all_files()
        
        if RICH_AVAILABLE:
            console.print(f"Processed [green]{success_smali}/{total_smali}[/green] .smali files")
        else:
            logger.info(f"Processed {success_smali}/{total_smali} .smali files")
        
        if RICH_AVAILABLE:
            console.print("[bold blue]Processing .xml files[/bold blue]")
        else:
            logger.info("Processing .xml files")
            
        xml_processor = XmlProcessor(self.config)
        total_xml, success_xml = xml_processor.process_all_files()
        
        if RICH_AVAILABLE:
            console.print(f"Processed [green]{success_xml}/{total_xml}[/green] .xml files")
        else:
            logger.info(f"Processed {success_xml}/{total_xml} .xml files")
        
        if RICH_AVAILABLE:
            summary_table = Table(title="Operation Summary", box=box.ROUNDED)
            summary_table.add_column("File Type", style="cyan")
            summary_table.add_column("Total Files", style="blue")
            summary_table.add_column("Processed", style="green")
            summary_table.add_column("Success Rate", style="yellow")
            
            smali_rate = f"{(success_smali/total_smali)*100:.1f}%" if total_smali > 0 else "N/A"
            xml_rate = f"{(success_xml/total_xml)*100:.1f}%" if total_xml > 0 else "N/A"
            
            summary_table.add_row("SMALI", str(total_smali), str(success_smali), smali_rate)
            summary_table.add_row("XML", str(total_xml), str(success_xml), xml_rate)
            
            console.print(summary_table)
            console.print("[bold green]WhatsApp cloning completed successfully![/bold green]")
        else:
            logger.info("Operation Summary:")
            logger.info(f"SMALI: {success_smali}/{total_smali} files processed")
            logger.info(f"XML: {success_xml}/{total_xml} files processed")
            logger.info("WhatsApp cloning completed successfully!")
        
        if RICH_AVAILABLE:
            with console.status("[bold green]Finalizing...", spinner="dots"):
                time.sleep(2)
            console.print("\n[bold green]All done! Enjoy your cloned WhatsApp.[/bold green]")
        else:
            for _ in range(3):
                chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
                for char in chars:
                    sys.stdout.write(f"\r{char} Finalizing...")
                    sys.stdout.flush()
                    time.sleep(0.1)
            print("\nAll done! Enjoy your cloned WhatsApp.")


def main():

    if len(sys.argv) > 1 and (sys.argv[1] == "-help" or sys.argv[1] == "--help" or 
                             sys.argv[1] == "-h"):
        show_help()
    
    try:
        cloner = WhatsAppCloner()
        cloner.display_intro()
        
        has_args = cloner.parse_arguments()
        
        if not has_args:
            cloner.setup_interactively()
            
        cloner.run()
        
    except KeyboardInterrupt:
        if RICH_AVAILABLE:
            console.print("\n\n[bold red]Process interrupted by user[/bold red]")
        else:
            print("\n\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")
            console.print_exception()
        else:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()