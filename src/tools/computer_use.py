import os
import sys
import base64
import io
from PIL import ImageGrab
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.utils.xml_formatter import xml_wrap
from src.utils.logging_config import logger
from src.utils.config_loader import load_config

# Load environment variables
load_dotenv()


class ComputerUseTool:
    def __init__(self):
        self.tool_name = "ComputerAgent"
        self.output_dir = "workspace/images"
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info("[ComputerUseTool] Initialized. Output dir: %s", self.output_dir)

    def take_screenshot(self) -> str:
        task_id = "task_screenshot_001"
        step = "computer_use::screenshot_capture"

        try:
            logger.debug("[ComputerUseTool] Taking screenshot...")
            screenshot = ImageGrab.grab()

            # Save screenshot to disk (optional for inspection)
            image_path = os.path.join(self.output_dir, "screenshot.png")
            screenshot.save(image_path, format="PNG")

            # Encode to base64
            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG")
            encoded_img = base64.b64encode(buffered.getvalue()).decode("utf-8")

            logger.info("[ComputerUseTool] Screenshot saved and base64 encoded.")

            return xml_wrap(
                task_id,
                "completed",
                step,
                tools_used=[{
                    "name": self.tool_name,
                    "status": "active",
                    "action": "take_screenshot",
                    "output": "Base64 screenshot image prepared for downstream analysis."
                }],
                reasoning={
                    "thought": "Captured screenshot from current desktop.",
                    "next_action": "Pass image to VisionTool for analysis."
                },
                result={
                    "success": True,
                    "data": encoded_img,
                    "errors": ""
                }
            )

        except Exception as e:
            logger.exception("[ComputerUseTool] Screenshot capture failed.")
            return xml_wrap(
                task_id,
                "failed",
                step,
                tools_used=[{
                    "name": self.tool_name,
                    "status": "failed",
                    "action": "take_screenshot",
                    "output": str(e)
                }],
                reasoning={
                    "thought": "Attempted to capture screenshot.",
                    "next_action": "Retry or notify user of failure."
                },
                result={
                    "success": False,
                    "data": "",
                    "errors": str(e)
                }
            )



