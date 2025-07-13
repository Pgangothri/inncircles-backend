import os
import sys
import base64
import io
import re
from PIL import Image, UnidentifiedImageError
import pytesseract

# ✅ Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from dotenv import load_dotenv
from src.utils.xml_formatter import xml_wrap
from src.utils.config_loader import load_config
from src.utils.logging_config import logger

# ✅ Load environment and config
load_dotenv()
tool_cfg = load_config("tools_config.yaml")
config = tool_cfg["tools"]["vision_tool"]

# ✅ Set Tesseract path from config or default
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class VisionTool:
    def __init__(self):
        self.tool_name = "VisionAgent"
        self.output_format = config.get("output_format", "base64")
        logger.info("[VisionTool] Initialized with output_format: %s", self.output_format)

    def analyze_base64_image(self, image_base64: str) -> str:
        logger.info("[VisionTool] Starting OCR analysis...")

        try:
            # ✅ Clean base64 (remove line breaks or extra whitespace)
            clean_base64 = image_base64.strip().replace("\n", "").replace("\r", "")
            image_data = base64.b64decode(clean_base64)

            # ✅ Load image safely
            try:
                image = Image.open(io.BytesIO(image_data)).convert("RGB")
            except UnidentifiedImageError as e:
                raise ValueError("Base64 input could not be parsed into a valid image.") from e

            logger.debug("[VisionTool] Image decoded successfully.")

            # ✅ Run OCR
            text = pytesseract.image_to_string(image)
            logger.info("[VisionTool] OCR completed.")

            return xml_wrap(
                task_id="task_vision_001",
                status="executing",
                current_step="vision_tool::screenshot_analysis",
                tools_used=[{
                    "name": self.tool_name,
                    "status": "active",
                    "action": "ocr_analysis",
                    "output": "Extracted text from image"
                }],
                reasoning={
                    "thought": "Performed OCR on the image to extract readable text.",
                    "next_action": "Use the text for downstream reasoning or parsing."
                },
                result={
                    "success": True,
                    "data": text.strip(),
                    "errors": ""
                }
            )

        except Exception as e:
            logger.exception("[VisionTool] OCR failed.")
            return xml_wrap(
                task_id="task_vision_001",
                status="failed",
                current_step="vision_tool::screenshot_analysis",
                tools_used=[{
                    "name": self.tool_name,
                    "status": "failed",
                    "action": "ocr_analysis",
                    "output": str(e)
                }],
                reasoning={
                    "thought": "OCR failed on the image input.",
                    "next_action": "Log the issue and possibly retry with cleaner image."
                },
                result={
                    "success": False,
                    "data": "",
                    "errors": str(e)
                }
            )



