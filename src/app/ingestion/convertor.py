import base64
import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader
from fastapi import UploadFile

class Converter:

    async def convert_file(self, file: UploadFile, filename: str) -> str:
        """Processa e converte um documento para texto"""
        try:
            # Salva o arquivo temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file.flush()
                
                # Processa o arquivo temporário
                loader = PyPDFLoader(temp_file.name)
                result = loader.load()
                
                # Limpa o arquivo temporário
                os.unlink(temp_file.name)
                
                # Retorna o texto concatenado de todas as páginas
                return "\n".join([page.page_content for page in result])
                    
        except Exception as e:
            print(f"Erro ao processar documento {filename}: {e}")
            raise

converter = Converter()