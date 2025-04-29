import os
import subprocess
import sys
import shutil
import time
import pickle
import requests

# === AUTO LIBRARY INSTALL ===
REQUIRED_LIBS = ["rich", "requests", "pyfiglet"]

def install_missing_libraries():
    for lib in REQUIRED_LIBS:
        try:
            __import__(lib)
        except ImportError:
            print(f"Installing missing library: {lib}")
            subprocess.call([sys.executable, "-m", "pip", "install", lib])

install_missing_libraries()

# === RE-IMPORT AFTER INSTALL ===
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint
import pyfiglet

# === STORAGE PERMISSION CHECK ===
def ensure_storage_permission():
    storage_path = os.path.expanduser("~/storage/shared")
    if not os.path.exists(storage_path):
        print("\n[!] Storage permission not granted.")
        print("[*] Requesting permission now...\n")
        subprocess.call(["termux-setup-storage"])
        print("\n[*] Please ALLOW storage access from the popup, then rerun the program.")
        sys.exit(1)

ensure_storage_permission()

# === CONFIG ===
LOGIN_URL = "http://localhost:8004/loginpy.php"
PROFILE_URL = "http://localhost:8004/profilepy.php"
COOKIE_FILE = "cookies.pkl"

console = Console()
ROOT = os.path.expanduser("~/storage/audiobooks/bwcyber_root")
session = requests.Session()

if not os.path.exists(ROOT):
    os.makedirs(ROOT)

current_dir = ROOT
logged_in = False
user_info = {}

# === COOKIE SYSTEM ===
def save_cookies():
    with open(COOKIE_FILE, "wb") as f:
        pickle.dump(session.cookies, f)

def load_cookies():
    global logged_in
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "rb") as f:
            session.cookies.update(pickle.load(f))
        try:
            response = session.get(PROFILE_URL)
            if response.status_code == 200 and response.json().get("status") == "success":
                global user_info
                user_info = response.json()['profile']
                logged_in = True
        except:
            pass

def clear_cookies():
    if os.path.exists(COOKIE_FILE):
        os.remove(COOKIE_FILE)

# === PATH SECURITY ===
def safe_path(path):
    real_path = os.path.abspath(path)
    if not real_path.startswith(ROOT):
        raise Exception("Access Denied: Outside root directory.")
    return real_path

# === BANNER ===
def show_banner():
    banner = pyfiglet.figlet_format("Bwcyber", font="big")
    console.clear()
    for line in banner.splitlines():
        rprint(f"[bold cyan]{line}[/]")
        time.sleep(0.01)
    
    if logged_in and user_info:
        user_details = (
            f"[bold yellow]User:[/] {user_info.get('username', 'N/A')}\n"
            f"[bold yellow]Email:[/] {user_info.get('email', 'N/A')}\n"
        )
        console.print(Panel.fit(user_details, title="Logged In Profile", style="bold blue"))
    else:
        console.print(Panel.fit("Simple Bwcyber Operating System", subtitle="Type [bold yellow]login <username> <password>[/] to begin", style="bold blue"))

# === HELP ===
def show_help():
    table = Table(title="Available Commands", title_style="bold magenta")
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description", style="green")
    table.add_row("ls", "List files/folders in current directory")
    table.add_row("cd <folder>", "Change directory")
    table.add_row("mkdir <folder>", "Create new folder")
    table.add_row("cat <file>", "View contents of a file")
    table.add_row("upload <path>", "Copy file from outside into root")
    table.add_row("download <file>", "Copy file from root to outside")
    table.add_row("git clone <url>", "Clone a Git repo into root")
    table.add_row("run <file.py>", "Run a Python script inside root")
    table.add_row("install <package>", "Install a Python library using pip")
    table.add_row("login <username> <password>", "Login using PHP API")
    table.add_row("logout", "Logout and clear session")
    table.add_row("clear", "Clear the terminal screen")
    table.add_row("help", "Show this help message")
    table.add_row("exit", "Exit the terminal")
    console.print(table)

# === SHELL ===
def shell():
    global current_dir, logged_in, user_info
    load_cookies()
    show_banner()

    while True:
        try:
            prompt_path = os.path.relpath(current_dir, ROOT)
            command = console.input(f"[cyan]root@bwcyber[/cyan] [bold magenta]/{prompt_path}>[/bold magenta]").strip()

            if command == "exit":
                console.print("Exiting...", style="bold red")
                break

            elif command == "help":
                show_help()

            elif command == "clear":
                show_banner()

            elif command.startswith("cd "):
                path = command[3:].strip()
                new_dir = safe_path(os.path.join(current_dir, path))
                if os.path.isdir(new_dir):
                    current_dir = new_dir
                else:
                    console.print("No such directory.", style="red")

            elif command == "ls":
                files = os.listdir(current_dir)
                if not files:
                    console.print("No files or folders.", style="dim")
                for f in files:
                    console.print(f"• {f}", style="bold green")

            elif command.startswith("mkdir "):
                name = command[6:].strip()
                os.mkdir(safe_path(os.path.join(current_dir, name)))
                console.print(f"Folder '{name}' created.", style="green")

            elif command.startswith("cat "):
                path = safe_path(os.path.join(current_dir, command[4:].strip()))
                with open(path) as f:
                    console.print(f.read(), style="dim")

            elif command.startswith("upload "):
                src = command[7:].strip()
                if not os.path.isfile(src):
                    console.print("Source file does not exist.", style="red")
                    continue
                dst = safe_path(os.path.join(current_dir, os.path.basename(src)))
                shutil.copy2(src, dst)
                console.print("File uploaded successfully.", style="green")

            elif command.startswith("download "):
                name = command[9:].strip()
                src = safe_path(os.path.join(current_dir, name))
                dst = os.path.abspath(name)
                shutil.copy2(src, dst)
                console.print("File downloaded successfully.", style="green")

            elif command.startswith("git clone "):
                url = command[10:].strip()
                console.print(f"Cloning from {url} ...", style="yellow")
                result = subprocess.run(["git", "clone", url], cwd=current_dir, capture_output=True, text=True)
                if result.returncode == 0:
                    console.print("Repository cloned successfully!", style="bold green")
                else:
                    console.print(result.stderr, style="bold red")

            elif command.startswith("run "):
                filename = command[4:].strip()
                file_path = safe_path(os.path.join(current_dir, filename))
                if os.path.isfile(file_path) and file_path.endswith(".py"):
                    console.print(f"Running {filename}...\n", style="yellow")
                    result = subprocess.run(["python", file_path], capture_output=True, text=True)
                    console.print(result.stdout, style="green")
                    if result.stderr:
                        console.print(result.stderr, style="red")
                else:
                    console.print("File not found or not a Python (.py) file.", style="red")

            elif command.startswith("install "):
                package = command[8:].strip()
                if package:
                    console.print(f"Installing {package}...", style="yellow")
                    result = subprocess.run([sys.executable, "-m", "pip", "install", package], capture_output=True, text=True)
                    if result.returncode == 0:
                        console.print(f"'{package}' installed successfully!", style="bold green")
                    else:
                        console.print(result.stderr, style="bold red")
                else:
                    console.print("Please specify a package to install.", style="red")

            elif command.startswith("login "):
                if logged_in:
                    console.print("Already logged in.", style="yellow")
                    continue
                parts = command.split()
                if len(parts) != 3:
                    console.print("Usage: login <username> <password>", style="yellow")
                    continue
                username, password = parts[1], parts[2]
                try:
                    response = session.post(LOGIN_URL, data={"username": username, "password": password})
                    if response.status_code == 200 and "success" in response.text.lower():
                        console.print("Login successful!", style="bold green")
                        logged_in = True
                        save_cookies()
                        profile_response = session.get(PROFILE_URL)
                        if profile_response.status_code == 200:
                            data = profile_response.json()
                            if data.get("status") == "success":
                                user_info = data['profile']
                        show_banner()
                    else:
                        console.print("Login failed. Check username/password.", style="bold red")
                except Exception as e:
                    console.print(f"[Login Error] {e}", style="red")

            elif command == "logout":
                if not logged_in:
                    console.print("You are not logged in.", style="red")
                    continue
                clear_cookies()
                logged_in = False
                user_info = {}
                console.print("Logged out successfully.", style="bold green")
                show_banner()

            else:
                if not logged_in and command.split()[0] not in ["login", "help", "clear", "exit"]:
                    console.print("Please login first to use this command.", style="bold red")
                    continue
                console.print(f"Unknown command: {command}", style="bold red")

        except Exception as e:
            console.print(f"[ERROR] {e}", style="bold red")

# === RUN ===
if __name__ == "__main__":
    shell()
