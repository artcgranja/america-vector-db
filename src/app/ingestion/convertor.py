import base64
import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader
from fastapi import UploadFile

class Converter:

    def convert_file(self, file_base64: UploadFile, filename: str) -> str:
        """Processa e converte um documento para texto"""
        try:
            result = PyPDFLoader(file_base64)
            return result.text_content
                    
        except Exception as e:
            print(f"Erro ao processar documento {filename}: {e}")
            raise

converter = Converter()