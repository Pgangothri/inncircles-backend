import os
import sys
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from io import BytesIO
from docx import Document
import re
# ✅ Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# ✅ Import using full path
from src.utils.config_loader import load_config
from src.utils.logging_config import logger

# ✅ Tesseract config for Windows (adjust path if needed)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class FilesTool:
    def __init__(self, folder: str = None):
        config = load_config("tools_config.yaml")
        default_path = config["tools"]["files_tool"].get("root_dir", "workspace")
        self.base_path = folder or default_path
        os.makedirs(self.base_path, exist_ok=True)
        logger.info(f"[FilesTool] Initialized with base path: {self.base_path}")

    def list_files(self, folder: str = None):
        scan_path = folder or self.base_path
        file_list = []
        for root, _, files in os.walk(scan_path):
            for file in files:
                file_list.append(os.path.join(root, file))
        logger.debug(f"[FilesTool] Found {len(file_list)} files in {scan_path}")
        return file_list

    def process_file(self, file_path):
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        logger.info(f"[FilesTool] Processing file: {file_path}")

        try:
            if ext == ".pdf":
                return self._extract_text_from_pdf(file_path)
            elif ext == ".docx":
                return self._extract_text_from_docx(file_path)
            else:
                logger.warning(f"[FilesTool] Unsupported file type: {ext}")
                return f"Unsupported file type: {ext}"
        except Exception as e:
            logger.error(f"[FilesTool] Failed processing file {file_path}: {e}")
            return f"Error processing file: {str(e)}"

    def _extract_text_from_docx(self, filepath):
        try:
            doc = Document(filepath)
            text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            logger.debug(f"[FilesTool] Extracted DOCX text from {filepath}")
            return text
        except Exception as e:
            logger.error(f"[FilesTool] DOCX extract failed: {e}")
            return f"Error extracting DOCX text: {str(e)}"

    def _extract_text_from_pdf(self, filepath):
        try:
            doc = fitz.open(filepath)
            text_chunks = []

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=300)
                img = Image.open(BytesIO(pix.tobytes("png")))
                page_text = pytesseract.image_to_string(img)
                text_chunks.append(f"[Page {page_num + 1}]\n{page_text.strip()}")

            logger.debug(f"[FilesTool] Extracted PDF OCR text from {filepath}")
            return "\n\n".join(text_chunks)
        except Exception as e:
            logger.error(f"[FilesTool] PDF extract failed: {e}")
            return f"Error extracting PDF text: {str(e)}"

    def extract_from_all(self, folder: str = None):
        scan_path = folder or self.base_path
        results = []
        for file in self.list_files(scan_path):
            content = self.process_file(file)
            results.append({
                "file": file,
                "content": content
            })
        logger.info(f"[FilesTool] Completed extraction from folder: {scan_path}")
        return results

    def extract_knowledge_documents(self, kb_folder: str) -> list:
        """Extracts all OCR text from files in the Knowledge_base folder"""
        kb_data = self.extract_from_all(kb_folder)
        kb_docs = []
        for item in kb_data:
            if isinstance(item["content"], str):
                kb_docs.append({
                    "source": item["file"],
                    "text": item["content"]
                })
        logger.info(f"[FilesTool] Extracted OCR content from {len(kb_docs)} knowledge documents")
        return kb_docs


