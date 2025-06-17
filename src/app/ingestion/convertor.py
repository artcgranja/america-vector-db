import base64
import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader
from fastapi import UploadFile

class Converter:

    async def convert_file(self, file: UploadFile, filename: str) -> str:
        """Processa e converte um documento para texto"""
        temp_file = None
        try:
            # Salva o arquivo temporariamente
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()
            temp_file.close()  # Fecha o arquivo antes de processá-lo
            
            # Processa o arquivo temporário
            loader = PyPDFLoader(temp_file.name)
            result = loader.load()
            
            # Limpa o arquivo temporário
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                print(f"Aviso: Não foi possível deletar arquivo temporário {temp_file.name}: {e}")
            
            # Retorna o texto concatenado de todas as páginas
            return "\n".join([page.page_content for page in result])
                
        except Exception as e:
            print(f"Erro ao processar documento {filename}: {e}")
            raise
        finally:
            # Garante que o arquivo temporário seja fechado
            if temp_file and not temp_file.closed:
                temp_file.close()
            # Tenta limpar o arquivo temporário se ainda existir
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except:
                    pass

converter = Converter()