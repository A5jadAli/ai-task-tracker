"""
Shortcuts-based actions library - uses keyboard shortcuts for reliable, deterministic actions.
These don't require AI decision-making - they're 100% reliable.
"""

import pyautogui
import time
import subprocess
import sys
import platform
import psutil
import os


class ShortcutsActionExecutor:
    """Executes common tasks using keyboard shortcuts - no AI needed."""

    def __init__(self):
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        self.platform = platform.system()

    # ==================== APPLICATION MANAGEMENT ====================

    def open_application(self, app_name, timeout=5):
        """
        Opens an application using shortcuts or command line.

        Args:
            app_name: Name of app or path (e.g., 'vscode', 'notepad', 'chrome', 'cmd')
            timeout: Wait time for app to open

        Returns:
            bool: True if successfully opened or already running
        """
        app_name_lower = app_name.lower().strip()

        try:
            # Check if already running
            if self.is_app_running(app_name):
                print(f"✓ {app_name} is already running")
                return True

            print(f"Opening {app_name}...")

            if self.platform == "Windows":
                try:
                    if app_name_lower in ["vscode", "code"]:
                        os.system("start code")
                    elif app_name_lower in ["notepad", "notepad.exe"]:
                        os.system("start notepad")
                    elif app_name_lower in ["cmd", "command"]:
                        os.system("start cmd")
                    elif app_name_lower in ["powershell", "pwsh"]:
                        os.system("start powershell")
                    elif app_name_lower in ["chrome", "google chrome"]:
                        os.system("start chrome")
                    elif app_name_lower in ["firefox"]:
                        os.system("start firefox")
                    elif app_name_lower in ["explorer", "file explorer"]:
                        os.system("start explorer")
                    else:
                        # Try direct execution
                        os.system(f"start {app_name}")
                except Exception as e:
                    print(f"Error launching app: {e}")
                    return False
            else:
                os.system(f"open {app_name}")

            # Wait for app to open
            time.sleep(timeout)

            if self.is_app_running(app_name):
                print(f"✓ {app_name} opened successfully")
                return True
            else:
                print(f"✗ Failed to open {app_name}")
                return False

        except Exception as e:
            print(f"✗ Error opening {app_name}: {e}")
            return False

    def close_application(self, app_name=None):
        """
        Closes current application or specified app.

        Args:
            app_name: Name of app to close (if None, closes current window)

        Returns:
            bool: True if closed
        """
        try:
            if app_name is None:
                # Close current window with Alt+F4
                pyautogui.hotkey("alt", "F4")
                print("✓ Closed current window")
            else:
                # Kill process by name
                for proc in psutil.process_iter(["pid", "name"]):
                    try:
                        if app_name.lower() in proc.info["name"].lower():
                            proc.kill()
                            print(f"✓ Closed {app_name}")
                            return True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            return True
        except Exception as e:
            print(f"✗ Error closing application: {e}")
            return False

    def is_app_running(self, app_name):
        """
        Checks if application is running.

        Args:
            app_name: Name of application

        Returns:
            bool: True if running
        """
        try:
            app_name_lower = app_name.lower().strip()
            
            # Remove common extensions for matching
            app_name_clean = app_name_lower.replace('.exe', '').replace('.app', '')
            
            # Common process name mappings
            process_name_map = {
                'vscode': ['code', 'code.exe'],
                'code': ['code', 'code.exe'],
                'notepad': ['notepad', 'notepad.exe'],
                'chrome': ['chrome', 'chrome.exe', 'google chrome'],
                'firefox': ['firefox', 'firefox.exe'],
                'cmd': ['cmd', 'cmd.exe'],
                'powershell': ['powershell', 'powershell.exe', 'pwsh', 'pwsh.exe'],
                'explorer': ['explorer', 'explorer.exe'],
            }
            
            # Get possible process names
            possible_names = process_name_map.get(app_name_clean, [app_name_clean])
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = proc.info['name'].lower()
                    
                    # Check if any possible name matches
                    for possible_name in possible_names:
                        if possible_name in proc_name or proc_name.replace('.exe', '') == possible_name:
                            return True
                    
                    # Fallback: check if app_name is substring of process name
                    if app_name_clean in proc_name:
                        return True
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return False
        except Exception as e:
            print(f"Error checking if {app_name} is running: {e}")
            return False

    # ==================== TAB MANAGEMENT ====================

    def switch_tab(self, direction="next", count=1):
        """
        Switch browser/editor tabs.

        Args:
            direction: 'next' or 'prev'
            count: Number of tabs to move

        Returns:
            bool: True if successful
        """
        try:
            key = "tab" if direction.lower() == "next" else "shift"
            modifier = ["ctrl"] if direction.lower() == "next" else ["ctrl", "shift"]

            for _ in range(count):
                if direction.lower() == "next":
                    pyautogui.hotkey("ctrl", "tab")
                else:
                    pyautogui.hotkey("ctrl", "shift", "tab")
                time.sleep(0.3)

            print(f"✓ Switched {count} tab(s) {direction}")
            return True
        except Exception as e:
            print(f"✗ Error switching tabs: {e}")
            return False

    def open_new_tab(self):
        """Opens a new tab in browser/editor."""
        try:
            pyautogui.hotkey("ctrl", "t")
            time.sleep(0.5)
            print("✓ Opened new tab")
            return True
        except Exception as e:
            print(f"✗ Error opening new tab: {e}")
            return False

    def close_tab(self):
        """Closes current tab."""
        try:
            pyautogui.hotkey("ctrl", "w")
            time.sleep(0.3)
            print("✓ Closed tab")
            return True
        except Exception as e:
            print(f"✗ Error closing tab: {e}")
            return False

    # ==================== FILE MANAGEMENT ====================

    def open_file(self, file_path):
        """
        Opens a file in the current application.

        Args:
            file_path: Path to file to open

        Returns:
            bool: True if successful
        """
        try:
            pyautogui.hotkey("ctrl", "o")
            time.sleep(1)
            pyautogui.write(file_path, interval=0.02)
            pyautogui.press("enter")
            time.sleep(1)
            print(f"✓ Opened file: {file_path}")
            return True
        except Exception as e:
            print(f"✗ Error opening file: {e}")
            return False

    def save_file(self):
        """Saves current file."""
        try:
            pyautogui.hotkey("ctrl", "s")
            time.sleep(0.5)
            print("✓ File saved")
            return True
        except Exception as e:
            print(f"✗ Error saving file: {e}")
            return False

    def save_as(self, file_path):
        """Saves file with new name/location."""
        try:
            pyautogui.hotkey("ctrl", "shift", "s")
            time.sleep(1)
            pyautogui.write(file_path, interval=0.02)
            pyautogui.press("enter")
            time.sleep(0.5)
            print(f"✓ Saved as: {file_path}")
            return True
        except Exception as e:
            print(f"✗ Error saving as: {e}")
            return False

    # ==================== EDITING ====================

    def type_text(self, text, interval=0.02):
        """Types text."""
        try:
            pyautogui.write(text, interval=interval)
            print(f"✓ Typed text")
            return True
        except Exception as e:
            print(f"✗ Error typing text: {e}")
            return False

    def paste_text(self):
        """Pastes from clipboard."""
        try:
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.3)
            print("✓ Pasted text")
            return True
        except Exception as e:
            print(f"✗ Error pasting: {e}")
            return False

    def copy_selection(self):
        """Copies selected text."""
        try:
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.3)
            print("✓ Copied selection")
            return True
        except Exception as e:
            print(f"✗ Error copying: {e}")
            return False

    def select_all(self):
        """Selects all content."""
        try:
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.3)
            print("✓ Selected all")
            return True
        except Exception as e:
            print(f"✗ Error selecting all: {e}")
            return False

    def undo(self):
        """Undo last action."""
        try:
            pyautogui.hotkey("ctrl", "z")
            time.sleep(0.3)
            print("✓ Undo executed")
            return True
        except Exception as e:
            print(f"✗ Error undo: {e}")
            return False

    def redo(self):
        """Redo last action."""
        try:
            pyautogui.hotkey("ctrl", "y")
            time.sleep(0.3)
            print("✓ Redo executed")
            return True
        except Exception as e:
            print(f"✗ Error redo: {e}")
            return False

    # ==================== NAVIGATION ====================

    def press_key(self, key, count=1):
        """Presses a key."""
        try:
            for _ in range(count):
                pyautogui.press(key)
                time.sleep(0.2)
            print(f"✓ Pressed key: {key}")
            return True
        except Exception as e:
            print(f"✗ Error pressing key: {e}")
            return False

    def hotkey(self, *keys):
        """Presses multiple keys together."""
        try:
            pyautogui.hotkey(*keys)
            time.sleep(0.3)
            print(f"✓ Pressed hotkey: {'+'.join(keys)}")
            return True
        except Exception as e:
            print(f"✗ Error with hotkey: {e}")
            return False

    # ==================== TERMINAL OPERATIONS ====================

    def run_command(self, command, app="cmd", wait_time=2):
        """
        Runs a terminal command.

        Args:
            command: Command to run (e.g., 'pip install flask')
            app: Terminal app ('cmd', 'powershell')
            wait_time: Wait after command execution

        Returns:
            bool: True if successful
        """
        try:
            # Open terminal
            if not self.open_application(app):
                return False

            time.sleep(1)

            # Type and execute command
            pyautogui.write(command, interval=0.02)
            pyautogui.press("enter")
            time.sleep(wait_time)

            print(f"✓ Executed command: {command}")
            return True
        except Exception as e:
            print(f"✗ Error running command: {e}")
            return False

    # ==================== WINDOW MANAGEMENT ====================

    def switch_window(self, direction="next"):
        """
        Switches between open windows.

        Args:
            direction: 'next' or 'prev'

        Returns:
            bool: True if successful
        """
        try:
            if direction.lower() == "next":
                pyautogui.hotkey("alt", "tab")
            else:
                pyautogui.hotkey("alt", "shift", "tab")
            time.sleep(0.5)
            print(f"✓ Switched window")
            return True
        except Exception as e:
            print(f"✗ Error switching window: {e}")
            return False

    def maximize_window(self):
        """Maximizes current window."""
        try:
            pyautogui.hotkey("alt", "F10")  # Windows maximize
            time.sleep(0.3)
            print("✓ Window maximized")
            return True
        except Exception as e:
            print(f"✗ Error maximizing window: {e}")
            return False

    def minimize_window(self):
        """Minimizes current window."""
        try:
            pyautogui.hotkey("win", "d")
            time.sleep(0.3)
            print("✓ Window minimized")
            return True
        except Exception as e:
            print(f"✗ Error minimizing window: {e}")
            return False
