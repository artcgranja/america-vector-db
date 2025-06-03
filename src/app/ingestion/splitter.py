from typing import List, Dict
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re

class LegalDocumentSplitter:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def _extract_sections(self, text: str) -> List[Dict]:
        # Regex patterns for legal document structure
        patterns = {
            "artigo": r"Art\.\s*\d+\.\s*[^\n]+",
            "paragrafo": r"§\s*\d+\.\s*[^\n]+",
            "inciso": r"[IVX]+\)\s*[^\n]+",
            "alinea": r"[a-z]\)\s*[^\n]+"
        }
        
        sections = []
        for section_type, pattern in patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                sections.append({
                    "type": section_type,
                    "content": match.group(),
                    "start": match.start(),
                    "end": match.end()
                })
        return sorted(sections, key=lambda x: x["start"])
    
    def split_document(self, documents: List[Document]) -> List[Document]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        enhanced_documents = []
        for doc in documents:
            sections = self._extract_sections(doc.page_content)
            
            # Create chunks preserving section boundaries
            chunks = []
            current_chunk = ""
            current_sections = []
            
            for section in sections:
                if len(current_chunk) + len(section["content"]) > self.chunk_size:
                    if current_chunk:
                        chunks.append({
                            "content": current_chunk,
                            "sections": current_sections
                        })
                    current_chunk = section["content"]
                    current_sections = [section["type"]]
                else:
                    current_chunk += "\n" + section["content"]
                    current_sections.append(section["type"])
            
            if current_chunk:
                chunks.append({
                    "content": current_chunk,
                    "sections": current_sections
                })
            
            # Create enhanced documents with section metadata
            for chunk in chunks:
                enhanced_metadata = doc.metadata.copy()
                enhanced_metadata.update({
                    "section_types": chunk["sections"],
                    "section_count": len(chunk["sections"])
                })
                enhanced_documents.append(
                    Document(
                        page_content=chunk["content"],
                        metadata=enhanced_metadata
                    )
                )
        
        return enhanced_documents