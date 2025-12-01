import pyautogui
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

class AgentVision:
    def __init__(self):
        self.screenshot_dir = "screenshots"
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)

    def capture_screen(self, with_grid=True):
        """Captures the screen and optionally overlays a grid."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.screenshot_dir}/screen_{timestamp}.png"
        
        screenshot = pyautogui.screenshot()
        
        if with_grid:
            self._overlay_grid(screenshot)

        screenshot.save(filename)
        return filename, screenshot.size

    def _overlay_grid(self, image):
        """Draws a 10x10 grid on the image with labels."""
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        # Grid settings
        rows = 10
        cols = 10
        step_x = width / cols
        step_y = height / rows
        
        # Draw lines
        for i in range(1, cols):
            x = i * step_x
            draw.line([(x, 0), (x, height)], fill="red", width=2)
            
        for i in range(1, rows):
            y = i * step_y
            draw.line([(0, y), (width, y)], fill="red", width=2)
            
        # Draw labels (0-1000 scale approximation)
        # We label the intersection points or cell centers?
        # Let's label the cell centers with their approximate 0-1000 coords
        try:
            # Try to load a default font, fallback if needed
            font = ImageFont.load_default()
        except:
            font = None

        for r in range(rows):
            for c in range(cols):
                # Center of the cell
                cx = int((c + 0.5) * step_x)
                cy = int((r + 0.5) * step_y)
                
                # Normalized coords (0-1000)
                norm_x = int((cx / width) * 1000)
                norm_y = int((cy / height) * 1000)
                
                label = f"{norm_x},{norm_y}"
                
                # Draw text with background for visibility
                bbox = draw.textbbox((cx, cy), label, font=font)
                draw.rectangle(bbox, fill="white")
                draw.text((cx, cy), label, fill="red", font=font)

    def get_screen_size(self):
        return pyautogui.size()
