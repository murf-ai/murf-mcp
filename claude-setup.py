#!/usr/bin/env python3.11

import json
import os
import platform
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional

class InstallationError(Exception):
    """Custom exception for installation errors."""
    pass

def get_uvx_path() -> str:
    """Get the path to uvx executable.
    
    Returns:
        str: Path to uvx executable
    """
    try:
        os_type = platform.system()
        command = 'which' if os_type in ("Linux", "Darwin") else 'where'
        result = subprocess.run([command, 'uvx'], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("Warning: uvx not found in PATH, defaulting to 'uvx'")
        return "uvx"

def update_config_file(config_path: Path) -> None:
    """Update Claude Desktop config with Murf MCP settings.
    
    Args:
        config_path: Path to config file
        
    Raises:
        FileNotFoundError: If config file not found
        json.JSONDecodeError: If config file is invalid JSON
    """
    if not config_path.exists():
        print(f"Config file does not exist at {config_path}")
        new_path = Path(input("Please enter the full path to the config file: "))
        if new_path.exists():
            update_config_file(new_path)
            return
        raise FileNotFoundError(f"Config file not found at {config_path}")

    print("Config file exists")
    
    murf_api_key = input("Please enter your Murf API key: ")
    
    try:
        config = json.loads(config_path.read_text())
    except json.JSONDecodeError:
        print("Config file is invalid JSON. Re-writing config file...")
        config = {}
    
    config.setdefault("mcpServers", {})
    
    uvx_path = get_uvx_path()
    config["mcpServers"]["Murf"] = {
        "command": uvx_path,
        "args": ["murf-mcp"],
        "env": {"MURF_API_KEY": murf_api_key}
    }
    
    config_path.write_text(json.dumps(config, indent=2))
    print("Config file updated successfully")

def detect_shell_config() -> Path:
    """Detect appropriate shell config file.
    
    Returns:
        Path: Path to shell config file
    """
    shell = os.environ.get("SHELL", "")
    home = Path.home()

    if "zsh" in shell:
        return home / ".zshrc"
    elif "bash" in shell:
        return home / ".bashrc"
    return home / ".profile"

def install_ffmpeg_windows() -> None:
    """Install FFmpeg on Windows."""
    def update_shell_config(ffmpeg_dir: str, config_file: Path) -> None:
        marker = "# >>> Added by murf-mcp to include ffmpeg from uv <<<"
        export_line = f'export PATH="{ffmpeg_dir}:$PATH"'

        if config_file.exists() and marker in config_file.read_text():
            print("✅ ffmpeg path already set in shell config")
            return

        with config_file.open("a") as f:
            f.write(f"\n{marker}\n{export_line}\n# <<< End of murf-mcp changes >>>\n")

        print(f"✅ ffmpeg path added to {config_file}. Restart your terminal or run:")
        print(f"   source {config_file}")

    def download_progress(block_num: int, block_size: int, total_size: int) -> None:
        if total_size > 0:
            percent = block_num * block_size * 100 / total_size
            sys.stdout.write(f"\rDownloading: {percent:.2f}%")
            sys.stdout.flush()

    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    install_dir = Path("C:/ffmpeg")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
        print("Downloading FFmpeg...")
        urllib.request.urlretrieve(url, tmp_zip.name, reporthook=download_progress)
        print("\nExtracting FFmpeg...")
        
        with zipfile.ZipFile(tmp_zip.name, 'r') as zip_ref:
            zip_ref.extractall(install_dir)

    try:
        os.unlink(tmp_zip.name)
    except OSError as e:
        print(f"Warning: Could not delete temp file {tmp_zip.name}: {e}")

    subdirs = [d for d in install_dir.iterdir() if d.is_dir()]
    if not subdirs:
        raise InstallationError("Could not find extracted FFmpeg directory")
    
    bin_path = subdirs[0] / "bin"
    print(f"Adding {bin_path} to user PATH...")

    try:
        import winreg as reg
    except ImportError:
        print(f"Warning: winreg module not found. Please manually add '{bin_path}' to system PATH")
        return

    with reg.OpenKey(reg.HKEY_CURRENT_USER, 'Environment', 0, reg.KEY_READ | reg.KEY_WRITE) as key:
        try:
            current_path, _ = reg.QueryValueEx(key, 'PATH')
        except FileNotFoundError:
            current_path = ''

        path_entries = current_path.split(os.pathsep)
        bin_path_str = str(bin_path)
        
        if bin_path_str not in path_entries:
            new_path = f"{current_path}{os.pathsep}{bin_path_str}" if current_path else bin_path_str
            reg.SetValueEx(key, 'PATH', 0, reg.REG_EXPAND_SZ, new_path)
            print(f"Added {bin_path} to PATH")
            
            config_file = detect_shell_config()
            update_shell_config(bin_path_str, config_file)
        else:
            print("FFmpeg path already in PATH")

    print("FFmpeg installed successfully")

def install_macos() -> None:
    """Install dependencies on macOS."""
    try:
        print(f"Python version: {platform.python_version()}")
        version = platform.python_version()
        major_minor = '.'.join(version.split('.')[:2])
        if major_minor != "3.11":
            print("Python version is not 3.11. Installing 3.11...")
            subprocess.run(["uv", "run", "--python", "pypy@3.11", "--", "python", "--version"], check=True)

        if subprocess.run(["which", "brew"], capture_output=True).returncode != 0:
            raise InstallationError("Homebrew is not installed. Please install Homebrew first")

        if subprocess.run(["which", "ffmpeg"], capture_output=True).returncode != 0:
            print("FFmpeg not found. Installing...")
            subprocess.run(["brew", "install", "ffmpeg"], check=True)
        else:
            print("FFmpeg already installed")

        config_path = Path("~/Library/Application Support/Claude/claude_desktop_config.json").expanduser()
        update_config_file(config_path)

    except subprocess.CalledProcessError as e:
        raise InstallationError(f"Command failed: {e.cmd}") from e

def install_windows() -> None:
    """Install dependencies on Windows."""
    try:
        print(f"Python version: {platform.python_version()}")
        version = platform.python_version()
        major_minor = '.'.join(version.split('.')[:2])
        if major_minor != "3.11":
            print("Python version is not 3.11. Installing 3.11...")
            subprocess.run(["uv", "run", "--python", "pypy@3.11", "--", "python", "--version"], check=True)

        if subprocess.run(["where", "ffmpeg"], capture_output=True).returncode != 0:
            print("FFmpeg not found. Installing...")
            install_ffmpeg_windows()
        else:
            print("FFmpeg already installed")

        config_path = Path(os.getenv('APPDATA', ''), "Claude", "claude_desktop_config.json")
        update_config_file(config_path)

    except subprocess.CalledProcessError as e:
        raise InstallationError(f"Command failed: {e.cmd}") from e

def main() -> None:
    """Main installation function."""
    try:
        os_type = platform.system()
        if os_type == "Linux":
            sys.exit("Linux installation not supported yet")
        elif os_type == "Darwin":
            print("Installing for macOS...")
            install_macos()
        elif os_type == "Windows":
            print("Installing for Windows...")
            install_windows()
        else:
            sys.exit(f"Unsupported OS: {os_type}")
    except InstallationError as e:
        sys.exit(f"Installation failed: {e}")
    except Exception as e:
        sys.exit(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()