""" File Processsor router module 
    Routes incoming file streams to the appropriate extractor based on file type.
    Supported file types: PDF and DOCX. 
"""

from typing import Union, BinaryIO
from pathlib import Path
import io 


#Import the respective extractors for PDF and DOCX
from src.extractors.pdf_extractor import PDFExtractor
from src.extractors.docx_extractor import DOCXExtractor

"""FileProcessor class handles routing of file streams to the appropriate extractor based on file type."""
class FileProcessor: 

    SUPPORTED_FILE_TYPES = {".pdf", ".docx", ".txt"}  # Extendable for future formats

    @classmethod
    def process_file(cls, file_source: Union[str, Path, BinaryIO, bytes], filename: str = "") -> str:
        """
        Extracts plain text from a supported file type (PDF, DOCX, or TXT) 
        
        : param file_source: File path (str or Path) or byte stream (BytesIO or raw bytes).
        : param filename: Optional filename to determine file type if file_source is a stream.
        : return Extracted text as a clean string. 
        """

        # Determine the file extension from file_name or path 

        extension = cls._get_extension(file_source, filename)

        #Can't process these file types 
        if extension not in cls.SUPPORTED_FILE_TYPES:
            raise ValueError(f"Unsupported file type: {extension}")

        if extension == ".pdf":
            return PDFExtractor.extract_text(file_source)

        elif extension == ".docx":
            return DOCXExtractor.extract_text(file_source)

        elif extension == ".txt":
            return cls._read_txt(file_source)
             
        else:
            raise ValueError(f"Unsupported file type: {extension}")


    @staticmethod 
    def _get_extension(file_source: Union[str, Path, BinaryIO, bytes], filename: str) -> str:
        """
        Determines the file extension from the file source or provided filename.
        
        :param file_source: File path (str or Path) or byte stream (BytesIO or raw bytes).
        :param filename: Optional filename to determine file type if file_source is a stream.
        :return: File extension as a string (e.g., '.pdf', '.docx', '.txt').
        """
        if filename:
            return Path(filename).suffix.lower()

        if isinstance(file_source, (str, Path)): 
            return Path(file_source).suffix.lower()
        
        if hasattr(file_source, "name") and file_source.name:
            return Path(file_source.name).suffix.lower()

        raise ValueError("Cannot determine file type from stream without a filename.")


    @staticmethod
    def _read_txt(file_source: Union[str, Path, BinaryIO, bytes]) -> str:
        """
        Reads text content from a TXT file source.
        
        :param file_source: File path (str or Path) or byte stream (BytesIO or raw bytes).
        :return: Extracted text as a string.
        """
        if isinstance(file_source, (str, Path)):
            with open(file_source, 'r', encoding='utf-8') as f:
                return f.read()

        if isinstance(file_source, bytes):
            return file_source.decode('utf-8')

        if hasattr(file_source, "read"):
            return file_source.read().decode('utf-8')

        raise ValueError("Unsupported TXT file source type.")


# Local testing of the FileProcessor
if __name__ == "__main__":
    sample_pdf_path = Path(__file__).parent.parent.parent / "data/sample.pdf"
    sample_docx_path = Path(__file__).parent.parent.parent / "data/sample.docx"
    sample_txt_path = Path(__file__).parent.parent.parent / "data/sample.txt"

    print("Extracted PDF Text:\n", FileProcessor.process_file(sample_pdf_path))
    print("\nExtracted DOCX Text:\n", FileProcessor.process_file(sample_docx_path))
    print("\nExtracted TXT Text:\n", FileProcessor.process_file(sample_txt_path))