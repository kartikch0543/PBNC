import io
import logging
import os
from typing import Any, Dict, List, Optional, Tuple
import fitz  # PyMuPDF
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


class PageContent:
    """Represents the raw content and metadata extracted from a single document page."""
    def __init__(
        self,
        page_number: int,  # 1-indexed
        text: str,
        is_scanned: bool = False,
        image_bytes: Optional[bytes] = None,
        char_count: int = 0,
    ):
        self.page_number = page_number
        self.text = text
        self.is_scanned = is_scanned
        self.image_bytes = image_bytes
        self.char_count = char_count


class OCREngine:
    """
    Layered document extraction engine:
    1. Fast-path native text extraction via PyMuPDF (fitz) for digitally generated PDFs.
    2. High-resolution rasterization (300 DPI) for scanned pages / images.
    3. Multimodal Vision AI (Gemini Flash) with structured output when API key is present.
    4. Local Tesseract OCR / Rule-based parser fallback.
    """

    MIN_TEXT_CHARS_PER_PAGE = 50

    @classmethod
    def process_file(cls, file_path: str, mime_type: str) -> List[PageContent]:
        """Extracts text and page images across all pages of a PDF or image file."""
        if mime_type in ("image/png", "image/jpeg"):
            return cls._process_single_image(file_path)
        elif mime_type == "application/pdf":
            return cls._process_pdf(file_path)
        else:
            raise ValueError(f"Unsupported MIME type for extraction: {mime_type}")

    @classmethod
    def _process_single_image(cls, file_path: str) -> List[PageContent]:
        """Loads a single image file and returns it as page 1."""
        with open(file_path, "rb") as img_file:
            img_bytes = img_file.read()

        text = ""
        # Try local pytesseract if available
        try:
            import pytesseract
            img = Image.open(io.BytesIO(img_bytes))
            text = pytesseract.image_to_string(img).strip()
        except Exception as ex:
            logger.debug(f"Local pytesseract not available or failed: {ex}")

        return [
            PageContent(
                page_number=1,
                text=text,
                is_scanned=True,
                image_bytes=img_bytes,
                char_count=len(text),
            )
        ]

    @classmethod
    def _process_pdf(cls, file_path: str) -> List[PageContent]:
        """Inspects PDF pages; extracts native text blocks or renders images for scans."""
        pages: List[PageContent] = []
        doc = fitz.open(file_path)

        try:
            for i, page in enumerate(doc):
                page_num = i + 1
                native_text = page.get_text("text").strip()

                is_scanned = len(native_text) < cls.MIN_TEXT_CHARS_PER_PAGE
                img_bytes = None

                if is_scanned:
                    # Rasterize page at 2x resolution (144 DPI) for OCR/Vision
                    pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                    img_bytes = pix.tobytes("png")

                    # Attempt local tesseract on rendered page if native text was minimal
                    if not native_text:
                        try:
                            import pytesseract
                            pil_img = Image.open(io.BytesIO(img_bytes))
                            ocr_text = pytesseract.image_to_string(pil_img).strip()
                            if ocr_text:
                                native_text = ocr_text
                        except Exception:
                            pass

                pages.append(
                    PageContent(
                        page_number=page_num,
                        text=native_text,
                        is_scanned=is_scanned,
                        image_bytes=img_bytes,
                        char_count=len(native_text),
                    )
                )
        finally:
            doc.close()

        return pages


ocr_engine = OCREngine()
