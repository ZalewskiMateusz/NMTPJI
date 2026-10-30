import os
import sys
import requests
import subprocess

GITHUB_REPO = "ZalewskiMateusz/NMTPJI"


def get_current_version():
    """Reads the current application version from the version.txt file."""
    try:
        # Handles path resolution for both raw Python scripts and frozen PyInstaller executables
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        version_path = os.path.join(base_path, "version.txt")

        if os.path.exists(version_path):
            with open(version_path, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception as e:
        print(f"[UPDATER ERROR] Could not read version.txt: {e}")

    return "1.0.0"


CURRENT_VERSION = get_current_version()


class AppUpdater:
    """Handles checking for updates and downloading new application releases from GitHub."""

    @staticmethod
    def check_for_updates():
        """Checks GitHub releases for a newer version than the current one."""
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("tag_name", "").lstrip("v")

                if latest_version and latest_version != CURRENT_VERSION:
                    # look for extension
                    assets = data.get("assets", [])
                    for asset in assets:
                        download_url = asset.get("browser_download_url")
                        file_name = asset.get("name")
                        if file_name.endswith(".exe"):
                            return True, latest_version, download_url
            return False, None, None
        except Exception as e:
            print(f"[UPDATER ERROR] Failed to check for updates: {e}")
            return False, None, None

    @staticmethod
    def download_and_update(download_url):
        """Downloads the new executable and triggers a silent updater script."""
        try:
            response = requests.get(download_url, stream=True, timeout=30)
            if response.status_code == 200:
                update_filename = "update_temp.exe"
                with open(update_filename, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                # Script for change
                current_exe = sys.executable
                batch_script = f"""
                @echo off
                timeout /t 2 /nobreak > nul
                del /f /q "{current_exe}"
                move /y "{update_filename}" "{current_exe}"
                start "" "{current_exe}"
                del "%~f0"
                """

                script_name = "update_process.bat"
                with open(script_name, "w") as batch_file:
                    batch_file.write(batch_script)

                subprocess.Popen(script_name, shell=True)
                sys.exit(0)
        except Exception as e:
            print(f"[UPDATER ERROR] Update installation failed: {e}")