import os
import base64
import tempfile
from typing import List, Union
from fastapi import UploadFile
from markitdown import MarkItDown
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document as LangchainDocument

class DocumentProcessor:
    """Processador de documentos para FastAPI"""
    
    def __init__(self, collection_name: str):
        """Inicializa o processador de documentos"""
        # Use a fixed 3072-dimensional embedder for high-dimensional vectors
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.collection_name = collection_name
        test_vec = self.embeddings.embed_query("test")
        if len(test_vec) != 3072:
            raise ValueError(f"Expected 3072-dimension embeddings, but got {len(test_vec)}")
        self.md_converter = MarkItDown(enable_plugins=True)
        
    def get_vectorstore(self) -> PGVector:
        """Conecta ao vectorstore PGVector via engine SQLAlchemy"""
        return PGVector(
            embeddings=self.embeddings,
            connection=os.getenv("DATABASE_URL"),
            collection_name=self.collection_name,
            use_jsonb=True
        )
    
    def process_document_text(self, markdown_text: str, doc_id: int, filename: str, document_type: str, parent_id: str = None) -> List[LangchainDocument]:
        """Processa texto markdown e gera chunks do LangChain"""
        langchain_doc = LangchainDocument(
            page_content=markdown_text,
            metadata={
                "source": filename,
                "doc_id": doc_id,
                "filename": filename,
                "document_type": document_type,
                "parent_id": int(parent_id) if parent_id else None,
                "hierarchy_level": 0 if parent_id is None else 1
            }
        )
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            add_start_index=True
        )
        return splitter.split_documents([langchain_doc])
    
    def create_vector_db_from_text(self, chunks: List[LangchainDocument]) -> int:
        """Cria ou atualiza o vector store com novos chunks, em lotes de 100"""
        db = self.get_vectorstore()
        batch_size = 250
        total = 0
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            db.add_documents(batch)
            total += len(batch)
        
        return total
    
    async def process_upload_file(self, file: UploadFile, doc_id: int, filename: str, document_type: str, parent_id: str = None) -> int:
        """Processa e vetoriza um documento a partir de um UploadFile"""
        try:
            content = await file.read()
            file_base64 = base64.b64encode(content).decode('utf-8')
            return self.process_and_store_document(file_base64, doc_id, filename, document_type, parent_id)
        except Exception as e:
            print(f"Erro ao processar documento {doc_id}: {e}")
            raise
    
    def process_and_store_document(self, file_base64: str, doc_id: int, filename: str, document_type: str, parent_id: str = None) -> int:
        """Processa e vetoriza um documento"""
        try:
            file_bytes = base64.b64decode(file_base64)
            
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file_bytes)
                temp_path = temp_file.name
            
            try:
                result = self.md_converter.convert(temp_path)
                markdown_text = result.text_content
                
                chunks = self.process_document_text(markdown_text, doc_id, filename, document_type, parent_id)
                return self.create_vector_db_from_text(chunks)
                
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            print(f"Erro ao processar documento {doc_id}: {e}")
            raise
    
    def delete_document_from_vector_db(self, doc_id: int) -> None:
        """Remove um documento do banco de dados do vector store"""
        vectorstore = self.get_vectorstore()
        vectorstore.delete(filter={"metadata": {"doc_id": doc_id}})