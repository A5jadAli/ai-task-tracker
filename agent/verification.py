"""
Verification system - checks if actions succeeded deterministically.
Uses process lists, file system, window titles - NOT AI/screenshots.
"""

import psutil
import os
import time
import subprocess
import pyautogui
from pathlib import Path


class Verifier:
    """Verifies that actions actually succeeded without AI interpretation."""

    def __init__(self):
        self.last_verification = None

    # ==================== APPLICATION VERIFICATION ====================

    def app_is_running(self, app_name, timeout=5):
        """
        Verifies if an application is running.

        Args:
            app_name: Name or partial name of application
            timeout: Max wait time for app to start

        Returns:
            bool: True if app is running
        """
        app_name_lower = app_name.lower()
        start_time = time.time()

        while time.time() - start_time < timeout:
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    if app_name_lower in proc.info["name"].lower():
                        print(f"✓ Verified: {app_name} is running")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            time.sleep(0.5)

        print(f"✗ Verification failed: {app_name} is not running")
        return False

    def app_is_closed(self, app_name, timeout=5):
        """
        Verifies if an application closed.

        Args:
            app_name: Name of application
            timeout: Max wait time for app to close

        Returns:
            bool: True if app is not running
        """
        app_name_lower = app_name.lower()
        start_time = time.time()

        while time.time() - start_time < timeout:
            found = False
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    if app_name_lower in proc.info["name"].lower():
                        found = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            if not found:
                print(f"✓ Verified: {app_name} is closed")
                return True
            time.sleep(0.5)

        print(f"✗ Verification failed: {app_name} is still running")
        return False

    # ==================== FILE VERIFICATION ====================

    def file_exists(self, file_path, timeout=5):
        """
        Verifies if a file exists.

        Args:
            file_path: Path to file
            timeout: Max wait time

        Returns:
            bool: True if file exists
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if os.path.isfile(file_path):
                print(f"✓ Verified: File exists at {file_path}")
                return True
            time.sleep(0.5)

        print(f"✗ Verification failed: File does not exist at {file_path}")
        return False

    def file_not_exists(self, file_path, timeout=5):
        """Verifies if a file does NOT exist."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if not os.path.isfile(file_path):
                print(f"✓ Verified: File does not exist at {file_path}")
                return True
            time.sleep(0.5)

        print(f"✗ Verification failed: File still exists at {file_path}")
        return False

    def file_has_content(self, file_path, min_size_bytes=1, timeout=5):
        """
        Verifies if a file has content.

        Args:
            file_path: Path to file
            min_size_bytes: Minimum file size in bytes
            timeout: Max wait time

        Returns:
            bool: True if file has content
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                if os.path.getsize(file_path) >= min_size_bytes:
                    print(
                        f"✓ Verified: File has content ({os.path.getsize(file_path)} bytes)"
                    )
                    return True
            except OSError:
                pass
            time.sleep(0.5)

        print(f"✗ Verification failed: File is empty or doesn't exist")
        return False

    def directory_exists(self, dir_path, timeout=5):
        """Verifies if a directory exists."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if os.path.isdir(dir_path):
                print(f"✓ Verified: Directory exists at {dir_path}")
                return True
            time.sleep(0.5)

        print(f"✗ Verification failed: Directory does not exist at {dir_path}")
        return False

    def directory_has_files(self, dir_path, min_files=1, timeout=5):
        """Verifies if a directory has files."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                files = os.listdir(dir_path)
                if len(files) >= min_files:
                    print(f"✓ Verified: Directory has {len(files)} items")
                    return True
            except OSError:
                pass
            time.sleep(0.5)

        print(f"✗ Verification failed: Directory is empty or doesn't exist")
        return False

    # ==================== TEXT CONTENT VERIFICATION ====================

    def file_contains_text(self, file_path, text_to_find, timeout=5):
        """
        Verifies if file contains specific text.

        Args:
            file_path: Path to file
            text_to_find: Text to search for
            timeout: Max wait time

        Returns:
            bool: True if text found
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if text_to_find in content:
                        print(f"✓ Verified: File contains '{text_to_find}'")
                        return True
            except OSError:
                pass
            time.sleep(0.5)

        print(f"✗ Verification failed: File does not contain '{text_to_find}'")
        return False

    # ==================== COMMAND OUTPUT VERIFICATION ====================

    def command_output_contains(self, command, text_to_find, timeout=10):
        """
        Verifies if command output contains text.

        Args:
            command: Command to run
            text_to_find: Text to search for in output
            timeout: Max wait time

        Returns:
            bool: True if text found in output
        """
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout
            )

            output = result.stdout + result.stderr
            if text_to_find in output:
                print(f"✓ Verified: Command output contains '{text_to_find}'")
                return True
            else:
                print(
                    f"✗ Verification failed: Command output doesn't contain '{text_to_find}'"
                )
                return False

        except subprocess.TimeoutExpired:
            print(f"✗ Verification failed: Command timeout")
            return False
        except Exception as e:
            print(f"✗ Verification failed: {e}")
            return False

    def command_succeeds(self, command, timeout=10):
        """
        Verifies if command executes successfully (exit code 0).

        Args:
            command: Command to run
            timeout: Max wait time

        Returns:
            bool: True if command succeeded
        """
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, timeout=timeout
            )

            if result.returncode == 0:
                print(f"✓ Verified: Command succeeded (exit code 0)")
                return True
            else:
                print(
                    f"✗ Verification failed: Command failed (exit code {result.returncode})"
                )
                return False

        except subprocess.TimeoutExpired:
            print(f"✗ Verification failed: Command timeout")
            return False
        except Exception as e:
            print(f"✗ Verification failed: {e}")
            return False

    # ==================== PACKAGE VERIFICATION ====================

    def package_is_installed(self, package_name, timeout=5):
        """
        Verifies if a Python package is installed.

        Args:
            package_name: Name of package
            timeout: Max wait time

        Returns:
            bool: True if package is installed
        """
        try:
            result = subprocess.run(
                f"pip show {package_name}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode == 0 and "Name:" in result.stdout:
                print(f"✓ Verified: Package '{package_name}' is installed")
                return True
            else:
                print(f"✗ Verification failed: Package '{package_name}' not found")
                return False

        except Exception as e:
            print(f"✗ Verification failed: {e}")
            return False

    # ==================== GENERIC VERIFICATION ====================

    def wait_for_condition(self, condition_func, timeout=5, check_interval=0.5):
        """
        Waits for a custom condition to be true.

        Args:
            condition_func: Function that returns True/False
            timeout: Max wait time
            check_interval: How often to check condition

        Returns:
            bool: True if condition becomes true within timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                if condition_func():
                    print(f"✓ Verified: Condition met")
                    return True
            except Exception as e:
                print(f"Condition check error: {e}")

            time.sleep(check_interval)

        print(f"✗ Verification failed: Condition not met within {timeout}s")
        return False


# Global verifier instance
verifier = Verifier()
