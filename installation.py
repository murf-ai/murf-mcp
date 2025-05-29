#!/usr/bin/env python3.11.11

import platform
import sys
import os
from pathlib import Path
import json
import urllib.request
import tempfile
import zipfile
import subprocess

def get_uvx_path():
    try:
        os_type = platform.system()
        if os_type == "Linux" or os_type == "Darwin":
            result = subprocess.run(['which', 'uvx'], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        elif os_type == "Windows":
            result = subprocess.run(['where', 'uvx'], capture_output=True, text=True, check=True)
            return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("Error: uvx not found in PATH. defaulting to 'uvx'")
        return "uvx"

def update_config_file(configFilePath):
    if os.path.exists(configFilePath):
        print("Config file already exists.")
        print(f"Read Permissions: {os.access(configFilePath, os.R_OK)}")
        murfAPIKey = input("Please enter your Murf API key: ")
        with open(configFilePath, "r+") as f:
            config = json.load(f)
            if config is None or config.get("mcpServers") is None:
                config = {
                    "mcpServers": {}
                }

            uvx_path = get_uvx_path()
            config["mcpServers"]["Murf"] = {
                        "command": uvx_path,
                        "args": ["murf-mcp"],
                        "env": {"MURF_API_KEY": murfAPIKey}
                }
            f.seek(0)
            json.dump(config, f, indent=2)
            f.truncate()
        print("Config file updated.")
    else:
        print(f"Config file does not exist at", configFilePath)
        new_path = input("Please enter the full path to the config file: ")
        if os.path.exists(new_path):
            update_config_file(Path(new_path))
        else:
            raise FileNotFoundError(f"Config file not found at", configFilePath)

def install_on_macOS():
    try:
        print(f"Python version: {platform.python_version()}")
        if (platform.python_version() != "3.11.11"):
            print("Python version is not 3.11.11. Installing 3.11.11...")
            subprocess.run(["uv", "run", "--python", "pypy@3.11.11", "--", "python", "--version"])
        result = subprocess.run(["which", "brew"], capture_output=True, text=True, check=True)
        if result.returncode != 0:
            print("Homebrew is not installed. Please install Homebrew first.")
            return
        result = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True, check=True)
        if result.returncode == 0:
            print("FFmpeg is already installed.")
        else:
            print("FFmpeg is not installed. Installing...")
            subprocess.run(["brew", "install", "ffmpeg"])
        # Update the config file
        configFilePath = Path("~/Library/Application Support/Claude/claude_desktop_config.json").expanduser()
        update_config_file(configFilePath)
    except FileNotFoundError as e:
        print(f"{e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred during installation: {e}")
        sys.exit(1)

def detect_shell_config():
    """Return the appropriate shell config file based on current shell."""
    shell = os.environ.get("SHELL", "")
    home = Path.home()

    if "zsh" in shell:
        return home / ".zshrc"
    elif "bash" in shell:
        return home / ".bashrc"
    else:
        return home / ".profile"


def install_ffmpeg_on_windows():
    def update_shell_config(ffmpeg_dir, config_file):
        """Add ffmpeg path to config file if not already present."""
        marker = "# >>> Added by murf-mcp to include ffmpeg from uv <<<"
        export_line = f'export PATH="{ffmpeg_dir}:$PATH"'

        config_text = config_file.read_text() if config_file.exists() else ""
        
        if marker in config_text:
            print("✅ ffmpeg path already set in shell config.")
            return

        with config_file.open("a") as f:
            f.write(f"\n{marker}\n{export_line}\n# <<< End of murf-mcp changes >>>\n")

        print(f"✅ ffmpeg path added to {config_file}. Restart your terminal or run:")
        print(f"   source {config_file}")

    def reporthook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = downloaded * 100 / total_size if total_size > 0 else 0
        sys.stdout.write(f"\rDownloading: {percent:.2f}%")
        sys.stdout.flush()
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    install_dir = Path("C:/ffmpeg") 

    # Download FFmpeg zip to temp dir
    print("Downloading FFmpeg...")
    tmp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    urllib.request.urlretrieve(url, tmp_zip.name, reporthook=reporthook)

    # Extract the zip
    print("Extracting FFmpeg...")
    with zipfile.ZipFile(tmp_zip.name, 'r') as zip_ref:
        zip_ref.extractall(install_dir)

    # Find the extracted folder and get its /bin path
    subdirs = [d for d in install_dir.iterdir() if d.is_dir()]
    if not subdirs:
        raise RuntimeError("Could not find extracted FFmpeg directory.")
    bin_path = subdirs[0] / "bin"

    # Add to user PATH (persistent)
    print(f"Adding {bin_path} to user PATH...")
    
        # cannot use setx as it has a cap on the length of the PATH variable
        # and it will truncate the PATH variable if it exceeds that limit
    reg_key = r'Environment'

    try:
        import winreg as reg
    except ImportError:
        print(f"winreg module not found. Please manually add the path '{str(bin_path)}' to your system PATH.")
        return

    with reg.OpenKey(reg.HKEY_CURRENT_USER, reg_key, 0, reg.KEY_READ | reg.KEY_WRITE) as key:
        try:
            current_path, _ = reg.QueryValueEx(key, 'PATH')
        except FileNotFoundError:
            current_path = ''
        print("Adding to PATH...")
        path_entries = current_path.split(os.pathsep)
        bin_path = str(bin_path)
        print(f"Bin Path: {bin_path} {type(bin_path)} ")
        print(path_entries)
        if bin_path not in path_entries:
            new_path_value = (current_path + os.pathsep + bin_path) if current_path else bin_path
            print(f"New PATH value: {new_path_value}")
            reg.SetValueEx(key, 'PATH', 0, reg.REG_EXPAND_SZ, new_path_value)
            print(f"Added {bin_path} to PATH.")
            config_file = detect_shell_config()
            update_shell_config(bin_path, config_file)
            print(f"Added {bin_path} to {config_file}.")
        else:
            print("FFmpeg path is already in PATH.")

    # Clean up
    try:
        os.unlink(tmp_zip.name)
    except OSError:
        print(f"Error deleting temporary file: {tmp_zip.name}")
    print("FFmpeg installed successfully.")

def install_on_windows():
    try:
        print(f"Python version: {platform.python_version()}")
        if (platform.python_version() != "3.11.11"):
            print("Python version is not 3.11.11. Installing 3.11.11...")
            subprocess.run(["uv", "run", "--python", "pypy@3.11.11", "--", "python", "--version"])
        result = subprocess.run(["where", "ffmpeg"], capture_output=True, text=True, check=True)
        if result.returncode == 0:
            print("FFmpeg is already installed.")
        else:
            print("FFmpeg is not installed. Installing...")
            install_ffmpeg_on_windows()
        # Update the config file
        configFilePath = Path(os.getenv('APPDATA'), "Claude", "claude_desktop_config.json")
        update_config_file(configFilePath)
    except FileNotFoundError as e:
        print(f"{e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred during installation: {e}")
        sys.exit(1)

def main():
    os_type = platform.system()
    if os_type == "Linux":
        print("Installing for Linux is not supported yet.")
    elif os_type == "Darwin":
       print("Running installation for macOS...")
       install_on_macOS()
    elif os_type == "Windows":
        print("Running installation for Windows...")
        install_on_windows()
    else:
        print(f"Unsupported OS: {os_type}")
        sys.exit(1)

main()