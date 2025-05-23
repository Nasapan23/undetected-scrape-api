#!/usr/bin/env python
"""
Script to install and configure stealth plugins for enhanced scraping
"""
import subprocess
import sys
import os
import platform
from pathlib import Path

CURRENT_DIR = Path(__file__).parent.absolute()
REQUIREMENTS_FILE = CURRENT_DIR / "requirements-extra.txt" 

def print_colored(text, color):
    """Print colored text in the terminal"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "end": "\033[0m"
    }
    
    print(f"{colors.get(color, '')}{text}{colors['end']}")

def check_python_version():
    """Check if Python version is compatible"""
    major, minor, _ = sys.version_info
    
    if major < 3 or (major == 3 and minor < 7):
        print_colored("Error: Python 3.7 or higher is required.", "red")
        sys.exit(1)
        
    print_colored(f"✓ Python version {major}.{minor} is compatible", "green")

def check_venv():
    """Check if running in a virtual environment"""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        print_colored("Warning: Not running in a virtual environment.", "yellow")
        response = input("Do you want to continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    else:
        print_colored("✓ Running in a virtual environment", "green")

def install_requirements():
    """Install requirements from the extra requirements file"""
    if not REQUIREMENTS_FILE.exists():
        print_colored(f"Error: Requirements file not found at {REQUIREMENTS_FILE}", "red")
        sys.exit(1)
        
    print_colored("Installing stealth plugins and dependencies...", "blue")
    
    try:
        # First update pip
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        print_colored("✓ Upgraded pip to latest version", "green")
        
        # Try installing with --no-dependencies first
        try:
            print_colored("Attempting to install packages individually...", "blue")
            with open(REQUIREMENTS_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            subprocess.run([sys.executable, "-m", "pip", "install", line], check=True)
                            print_colored(f"✓ Installed {line}", "green")
                        except subprocess.CalledProcessError:
                            print_colored(f"Warning: Couldn't install {line}, will try alternative", "yellow")
        except Exception as e:
            print_colored(f"Warning: Error during individual installation: {e}", "yellow")
            
        # Now try the full requirements file
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)], check=True)
            print_colored("✓ Successfully installed stealth plugins", "green")
        except subprocess.CalledProcessError as e:
            print_colored(f"Warning: Some packages could not be installed from requirements file", "yellow")
            print_colored("    Some stealth features may be limited, but the application will still work", "yellow")
            print_colored(f"    Original error: {e}", "yellow")
    except Exception as e:
        print_colored(f"Error installing requirements: {e}", "red")
        print_colored("The application will still work but with limited stealth capabilities", "yellow")

def install_playwright_browsers():
    """Install Playwright browsers"""
    print_colored("Installing Playwright browsers...", "blue")
    
    try:
        # Install only chromium to save space and time
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        subprocess.run([sys.executable, "-m", "playwright", "install-deps", "chromium"], check=True)
        print_colored("✓ Successfully installed Playwright browsers", "green")
    except subprocess.CalledProcessError as e:
        print_colored(f"Error installing Playwright browsers: {e}", "red")
        print_colored("Please try installing manually with:", "yellow")
        print_colored("    python -m playwright install chromium", "yellow")
        print_colored("    python -m playwright install-deps chromium", "yellow")

def create_data_dirs():
    """Create necessary data directories"""
    data_dir = CURRENT_DIR / "data"
    cookie_dir = data_dir / "cookies"
    
    print_colored("Creating data directories...", "blue")
    
    data_dir.mkdir(exist_ok=True)
    cookie_dir.mkdir(exist_ok=True)
    
    print_colored("✓ Created data directories", "green")

def main():
    """Main function"""
    print_colored("=== Undetectable Scraper: Stealth Plugin Installer ===", "cyan")
    
    check_python_version()
    check_venv()
    install_requirements()
    install_playwright_browsers()
    create_data_dirs()
    
    print_colored("\nSetup complete! You can now use enhanced anti-detection features.", "green")
    print_colored("\nQuick start:", "blue")
    print_colored("1. Make sure to set USE_UNDETECTED=true in your .env file", "yellow")
    print_colored("2. Run the application with 'python run.py'", "yellow")
    print_colored("3. For challenging sites, try DISABLE_HEADLESS=true", "yellow")

if __name__ == "__main__":
    main() 