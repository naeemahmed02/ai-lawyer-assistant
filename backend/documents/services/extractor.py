from docling.document_converter import DocumentConverter
from docling.datamodel.document import ConversionResult
import os

class DocConverter:
    """
    A utility class for converting documents using Docling's DocumentConverter.
    """

    def __init__(self, converter: DocumentConverter):
        """
        Initialize the DocConverter with a shared converter instance.

        Args:
            converter (DocumentConverter): Shared instance of the Docling document converter.
        """
        self.converter = converter
    
    def convert_document(self, file_path: str) -> ConversionResult:
        """
        Convert the document located at the given file path.

        Args:
            file_path (str): Path to the document that needs conversion.

        Returns:
            ConversionResult: The rich conversion result object from Docling.
            
        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} was not found.")
            
        try:
            # Performs the actual extraction
            result = self.converter.convert(file_path)
            return result
        except Exception as e:
            print(f"Error converting document {file_path}: {e}")
            raise


if __name__ == "__main__":
    # 1. Initialize the heavy AI model ONLY ONCE globally
    shared_converter = DocumentConverter()
    
    # 2. Inject the shared model into your utility worker class
    worker = DocConverter(converter=shared_converter)
    
    # 3. You can now efficiently process multiple legal files in a loop
    files_to_process = ["backend/documents/2026/05/25/AIResume.pdf"] 
    
    for file_path in files_to_process:
        if os.path.exists(file_path): # Basic safety check for example run
            result = worker.convert_document(file_path)
            
            # To get your Markdown text out for your RAG system:
            markdown_output = result.document.export_to_markdown()
            print(markdown_output) # Print first 500 characters
