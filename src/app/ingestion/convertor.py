import base64
import os
import tempfile
from markitdown import MarkItDown
from fastapi import UploadFile

class Converter:
    def __init__(self):
        self.md_converter = MarkItDown(enable_plugins=True)

    def convert_to_markdown(self, file_base64: UploadFile, filename: str) -> str:
        """Processa e vetoriza um documento"""
        try:
            file_content = file_base64.read()
            
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file_content)
                temp_path = temp_file.name
            
            try:
                result = self.md_converter.convert(temp_path)
                markdown_text = result.text_content
                return markdown_text
            
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            print(f"Erro ao processar documento {filename}: {e}")
            raise

converter = Converter()