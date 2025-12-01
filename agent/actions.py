import pyautogui
import time
import platform

class ActionExecutor:
    def __init__(self):
        # Safety: Fail-safe is enabled by default in pyautogui
        pyautogui.FAILSAFE = True
        # Add a small pause between actions to make it visible/safer
        pyautogui.PAUSE = 1.0 

    def move_mouse(self, x, y):
        """Moves the mouse to the specified coordinates."""
        print(f"Action: Moving mouse to ({x}, {y})")
        pyautogui.moveTo(x, y, duration=0.5) # Visible movement

    def click(self, x=None, y=None, clicks=1, button='left'):
        """Clicks at the current position or specified coordinates."""
        if x is not None and y is not None:
            self.move_mouse(x, y)
        
        print(f"Action: Clicking {button} button {clicks} time(s)")
        pyautogui.click(clicks=clicks, button=button)

    def type_text(self, text, interval=0.05):
        """Types text with a delay between keystrokes."""
        print(f"Action: Typing '{text}'")
        pyautogui.write(text, interval=interval)

    def press_key(self, key):
        """Presses a specific key (e.g., 'enter', 'esc', 'win')."""
        print(f"Action: Pressing key '{key}'")
        pyautogui.press(key)

    def hotkey(self, *keys):
        """Presses a combination of keys (e.g., 'ctrl', 'c')."""
        print(f"Action: Pressing hotkey {'+'.join(keys)}")
        pyautogui.hotkey(*keys)

    def scroll(self, amount):
        """Scrolls the screen."""
        print(f"Action: Scrolling {amount}")
        pyautogui.scroll(amount)
