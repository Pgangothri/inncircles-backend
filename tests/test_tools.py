import os
import sys
import re
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from tools.files_tool import FilesTool
from tools.code_interpreter import CodeInterpreterTool
from tools.shell_tool import ShellTool
from tools.web_search import WebSearchTool
from tools.computer_use import ComputerUseTool
from tools.vision_tool import VisionTool


class TestToolSuite(unittest.TestCase):

    def test_files_tool(self):
        folder_path = "workspace/Form"
        tool = FilesTool(folder=folder_path)
        results = tool.extract_from_all()
        all_text = " ".join([r["content"] for r in results])
        print("\n[✅ FilesTool] Preview:\n", all_text[:300])

        self.assertGreater(len(results), 0, "[❌ FilesTool] No files processed")

    def test_code_interpreter(self):
        tool = CodeInterpreterTool()
        code = "result = 5 * 5\nprint(result)"
        result = tool.execute(code, safety=True)
        print("\n[✅ CodeInterpreterTool] Output:\n", result)

        match = re.search(r"<data>(.*?)</data>", result, re.DOTALL)
        self.assertIsNotNone(match, "[❌ CodeInterpreterTool] <data> tag not found")

        output_value = match.group(1).strip()
        self.assertEqual(output_value, "25", f"[❌ CodeInterpreterTool] Incorrect result: {output_value}")

    def test_shell_tool(self):
        tool = ShellTool()
        result = tool.execute("echo Hello Agent")
        print("\n[✅ ShellTool] Output:\n", result)
        self.assertIn("Hello Agent", result, "[❌ ShellTool] Echo failed")

    def test_web_search(self):
        tool = WebSearchTool()
        result = tool.execute("Hello")
        print("\n[✅ WebSearchTool] Output:\n", result[:500])
        self.assertTrue(
    any(status in result for status in ["<status>ok</status>", "<status>empty</status>", "<status>completed</status>"]),
    "[❌ WebSearchTool] Unexpected status"
)


    def test_computer_use_tool(self):
        tool = ComputerUseTool()
        result = tool.take_screenshot()
        print("\n[✅ ComputerUseTool] Screenshot XML:\n", result[:300])
        self.assertIn("<status>", result, "[❌ ComputerUseTool] Screenshot failed")

    def test_vision_tool(self):
        print("\n[ℹ️ VisionTool] Capturing screenshot...")
        screenshot_xml = ComputerUseTool().take_screenshot()
        match = re.search(r"<data>(.*?)</data>", screenshot_xml, re.DOTALL)
        self.assertIsNotNone(match, "[⚠️ VisionTool] No base64 image found in screenshot")

        base64_image = match.group(1).strip()
        tool = VisionTool()
        result = tool.analyze_base64_image(base64_image)
        print("\n[✅ VisionTool] Output:\n", result[:300])

        ocr_match = re.search(r"<data>(.*?)</data>", result, re.DOTALL)
        self.assertIsNotNone(ocr_match, "[❌ VisionTool] OCR text not found")
        self.assertIn("<status>", result, "[❌ VisionTool] Missing status tag")


if __name__ == "__main__":
    unittest.main()
