"""
PDF Text Extractor Module
Handles text extraction from PDF files via file path or raw bytes stream.
"""

from typing import List, Union, BinaryIO
import io
import pdfplumber
from pathlib import Path


class PDFExtractor:
    
    """Extracts raw text content page-by-page from PDF documents."""
    @staticmethod
    def extract_text(file_source: Union[str, BinaryIO, bytes]) -> str:
        """
        Extracts all text from a PDF source.
        
        :param file_source: File path (str), byte stream (BytesIO), or raw bytes.
        :return: Extracted text string separated by page linebreaks.
        """
        pdf_stream = file_source
        if isinstance(file_source, bytes):
            pdf_stream = io.BytesIO(file_source)

        pages_text: List[str] = []

        try:
            with pdfplumber.open(pdf_stream) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text(layout=True)
                    if text:
                        pages_text.append(text)
                    else:
                        pages_text.append(f"[Warning: No extractable text on page {page_num}]")
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from PDF: {str(e)}") from e

        return "\n\n".join(pages_text)

    @staticmethod
    def extract_pages(file_source: Union[str, BinaryIO, bytes]) -> List[dict]:
        """
        Extracts text indexed by page number for detailed document processing.
        
        :return: List of dicts containing page_number and page_text.
        """
        pdf_stream = file_source
        if isinstance(file_source, bytes):
            pdf_stream = io.BytesIO(file_source)

        pages = []
        with pdfplumber.open(pdf_stream) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                pages.append({"page_number": i, "text": text})

        return pages

# Local testing of extracting PDF text
if __name__ == "__main__":

    sample_pdf_path = Path(__file__).parent.parent.parent / "data/sample.pdf"
    # Example usage / sanity check
    # text = PDFExtractor.extract_text("sample_invoice.pdf")
    print(PDFExtractor.extract_text(sample_pdf_path))
