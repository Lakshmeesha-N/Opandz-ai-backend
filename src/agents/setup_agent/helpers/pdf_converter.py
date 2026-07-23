# src/agents/setup_agent/helpers/pdf_converter.py
import os
import logging

logger = logging.getLogger(__name__)

def convert_pdf_to_docx(pdf_path: str, docx_path: str) -> bool:
    """
    Converts a PDF file to a DOCX file using pdf2docx.
    Returns True if successful, False otherwise.
    """
    try:
        from pdf2docx import Converter
        cv = Converter(pdf_path)
        cv.convert(docx_path)      # all pages by default
        cv.close()
        logger.info(f"[pdf_converter] Successfully converted {pdf_path} to {docx_path}")
        return True
    except Exception as e:
        logger.exception(f"[pdf_converter] Failed to convert {pdf_path} to DOCX: {e}")
        return False

