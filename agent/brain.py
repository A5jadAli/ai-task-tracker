import os
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv
import json
import base64
import pyautogui

load_dotenv()


class AgentBrain:
    def __init__(self):
        self.primary_provider = os.getenv("MODEL_PROVIDER", "gemini")
        self.gemini_model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash-exp")
        self.openai_model_name = "gpt-4o"

        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # Configure Gemini
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel(self.gemini_model_name)

        # Configure OpenAI
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None

        # Screen dimensions for scaling
        self.screen_width, self.screen_height = pyautogui.size()

    def _get_prompt(self, goal, history):
        return f"""
        You are an AI agent controlling a computer.
        GOAL: {goal}
        
        HISTORY:
        {history}

        The screenshot has a RED GRID overlay.
        The labels represent the (x, y) coordinates in a 0-1000 scale.
        
        INSTRUCTIONS:
        1. Look at the screenshot to understand the current state.
        2. Decide the best action to achieve the GOAL.
        
        CRITICAL STRATEGY FOR RELIABILITY:
        - **PREFER KEYBOARD SHORTCUTS**: They are 100% reliable. 
          - To open Start Menu: Use `press_key('win')` (DO NOT CLICK the start icon).
          - To Search: Press 'win', then `type_text('query')`.
          - To Switch Apps: Use `hotkey('alt', 'tab')`.
          - To Close App: Use `hotkey('alt', 'f4')`.
        - Only use `click(x, y)` for specific UI elements inside apps that don't have shortcuts.
        
        3. If you MUST click:
           - Estimate center coordinates based on the RED GRID (0-1000 scale).
           - Verify if the previous click worked. If not, try a slightly different spot.

        Available actions:
        - move_mouse(x, y): x and y are 0-1000 normalized coordinates.
        - click(x, y, button='left', clicks=1): x and y are 0-1000 normalized coordinates.
        - type_text(text)
        - press_key(key): e.g., 'enter', 'win', 'esc'
        - hotkey(*keys): pass as list in JSON: "params": {{"keys": ["ctrl", "c"]}}
        - done(): Call this ONLY when the goal is visibly achieved.

        Example Response (Opening Notepad):
        {{{{
            "thought": "The goal is to open Notepad. The most reliable way is to press the Windows key and search.",
            "action": "press_key",
            "params": {{"key": "win"}}
        }}}}
        
        IMPORTANT: Return ONLY raw JSON. No markdown formatting.
        """

    def think(self, goal, screenshot_path, history=[]):
        """
        Analyzes the screenshot and history to decide the next action.
        """
        result = {"error": "No provider available"}

        # Try Gemini First
        if self.primary_provider == "gemini":
            result = self._think_gemini(goal, screenshot_path, history)

            if "error" in result and (
                "429" in str(result["error"]) or "quota" in str(result["error"]).lower()
            ):
                print(f"⚠️ Gemini Quota Exceeded. Falling back to OpenAI...")
                return self._think_openai(goal, screenshot_path, history)

            return self._scale_coordinates(result)

        # If primary is OpenAI
        elif self.primary_provider == "openai":
            result = self._think_openai(goal, screenshot_path, history)
            return self._scale_coordinates(result)

        return result

    def _scale_coordinates(self, decision):
        """Scales 0-1000 coordinates to actual screen pixels."""
        if "params" in decision:
            params = decision["params"]
            if "x" in params:
                params["x"] = int((params["x"] / 1000) * self.screen_width)
            if "y" in params:
                params["y"] = int((params["y"] / 1000) * self.screen_height)
            decision["params"] = params
        return decision

    def _think_gemini(self, goal, screenshot_path, history):
        if not self.gemini_model:
            return {"error": "Gemini API Key not configured"}

        try:
            prompt = self._get_prompt(goal, history)
            img = genai.upload_file(screenshot_path)
            response = self.gemini_model.generate_content([prompt, img])

            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]

            return json.loads(text)
        except Exception as e:
            return {"error": str(e)}

    def _think_openai(self, goal, screenshot_path, history):
        if not self.openai_client:
            return {"error": "OpenAI API Key not found"}

        try:
            prompt = self._get_prompt(goal, history)
            with open(screenshot_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")

            response = self.openai_client.chat.completions.create(
                model=self.openai_model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            return {"error": str(e)}

    def think_about_task(self, objective):
        """
        For AI-only tasks (not vision-based).
        Used when agent needs to write code, provide instructions, etc.

        Args:
            objective: What the AI should do

        Returns:
            dict: AI's response with thought, action_type, and content
        """
        prompt = f"""
        OBJECTIVE: {objective}
        
        You are an AI assistant helping a user accomplish a task.
        Provide your response in JSON format with:
        - "thought": Your reasoning about what to do
        - "action_type": Either "code", "instructions", or "analysis"
        - "content": The actual response (code, step-by-step instructions, or analysis)
        
        IMPORTANT: Return ONLY raw JSON. No markdown formatting or code blocks.
        """

        try:
            if self.primary_provider == "gemini" and self.gemini_model:
                response = self.gemini_model.generate_content(prompt)
                text = response.text.strip()

                # Clean up markdown if present
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]

                return json.loads(text)

            elif self.primary_provider == "openai" and self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=self.openai_model_name,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content
                return json.loads(content)

            else:
                return {"error": "No AI provider available"}

        except Exception as e:
            return {"error": str(e)}
