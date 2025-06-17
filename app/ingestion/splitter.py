from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document as LangchainDocument
from app.core.config import settings

class DocumentProcessor:
    """Processador de documentos para FastAPI"""
    
    def __init__(self, collection_name: str):
        """Inicializa o processador de documentos"""
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.collection_name = collection_name
        self.vectorstore = self.get_vectorstore()
        test_vec = self.embeddings.embed_query("test")
        if len(test_vec) != 3072:
            raise ValueError(f"Expected 3072-dimension embeddings, but got {len(test_vec)}")
        
    def get_vectorstore(self) -> PGVector:
        """Conecta ao vectorstore PGVector via engine SQLAlchemy"""
        return PGVector(
            embeddings=self.embeddings,
            connection=settings.database_url,
            collection_name=self.collection_name,
            use_jsonb=True
        )
    
    def process_document_text(self, md_text: str, doc_id: int, filename: str, document_type: str, parent_id: str = None, subjects: List[str] = None) -> List[LangchainDocument]:
        """Processa texto markdown e gera chunks do LangChain"""
        langchain_doc = LangchainDocument(
            page_content=md_text,
            metadata={
                "source": filename,
                "doc_id": doc_id,
                "document_type": document_type,
                "parent_id": int(parent_id) if parent_id else None,
                "hierarchy_level": 0 if parent_id is None else 1,
                "subjects": subjects
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
    
    def process_and_store_document(self, md_text: str, doc_id: int, filename: str, document_type: str, parent_id: str = None, subjects: List[str] = None) -> int:
        """Processa e vetoriza um documento"""
        try:
            chunks = self.process_document_text(md_text, doc_id, filename, document_type, parent_id, subjects)
            return self.create_vector_db_from_text(chunks)
                    
        except Exception as e:
            print(f"Erro ao processar documento {doc_id}: {e}")
            raise
    
    def delete_document_from_vector_db(self, doc_id: int) -> None:
        """Remove um documento do banco de dados do vector store"""
        try:
            docs = self.vectorstore.similarity_search(query="", k=100, filter={"doc_id": doc_id})
            ids_to_delete = [doc.id for doc in docs]
            self.vectorstore.delete(ids=ids_to_delete)
        except Exception as e:
            print(f"Erro ao deletar documento {doc_id}: {e}")
            raise
    
    def delete_all_documents_from_vector_db(self) -> None:
        """Remove todos os documentos do banco de dados do vector store"""
        return self.vectorstore.delete(filter={"metadata": {}})