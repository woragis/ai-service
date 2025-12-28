"""
RAG (Retrieval-Augmented Generation) engine for agent knowledge bases.

Combines vector database search with document retrieval to provide context for LLM responses.
"""

from typing import List, Dict, Any, Optional
from app.knowledge_base.vector_db import get_vector_db, VectorDBProvider
from app.knowledge_base.file_storage import get_file_storage, FileStorageProvider
from app.logger import get_logger

logger = get_logger()


class RAGEngine:
    """RAG engine for retrieving relevant context from knowledge base."""
    
    def __init__(
        self,
        vector_db: Optional[VectorDBProvider] = None,
        file_storage: Optional[FileStorageProvider] = None
    ):
        self.vector_db = vector_db or get_vector_db()
        self.file_storage = file_storage or get_file_storage()
        self.logger = get_logger()
    
    async def retrieve_context(
        self,
        query: str,
        collection: str,
        document_paths: Optional[List[str]] = None,
        top_k: int = 5,
        score_threshold: float = 0.7
    ) -> str:
        """
        Retrieve relevant context for a query using RAG.
        
        Args:
            query: User query
            collection: Vector DB collection name
            document_paths: Optional list of document paths to search
            top_k: Number of results to retrieve
            score_threshold: Minimum similarity score
        
        Returns:
            Combined context string
        """
        context_parts = []
        
        # 1. Search vector database
        if self.vector_db:
            try:
                vector_results = self.vector_db.search(
                    query=query,
                    collection=collection,
                    top_k=top_k,
                    score_threshold=score_threshold
                )
                
                for result in vector_results:
                    if "text" in result:
                        context_parts.append(result["text"])
                    elif "content" in result:
                        context_parts.append(result["content"])
            except Exception as e:
                self.logger.warn("Vector DB search failed", error=str(e), collection=collection)
        
        # 2. Retrieve from document storage
        if document_paths and self.file_storage:
            for doc_path in document_paths:
                try:
                    content = self.file_storage.read_file(doc_path)
                    if content:
                        context_parts.append(content)
                except Exception as e:
                    self.logger.warn("Failed to read document", error=str(e), path=doc_path)
        
        # Combine context
        context = "\n\n".join(context_parts)
        
        if context:
            self.logger.info(
                "RAG context retrieved",
                collection=collection,
                context_length=len(context),
                sources=len(context_parts)
            )
        else:
            self.logger.warn("No RAG context retrieved", collection=collection, query=query)
        
        return context
    
    def format_context_for_prompt(self, context: str, max_length: int = 2000) -> str:
        """
        Format context for inclusion in LLM prompt.
        
        Args:
            context: Raw context string
            max_length: Maximum length to include
        
        Returns:
            Formatted context string
        """
        if not context:
            return ""
        
        # Truncate if too long
        if len(context) > max_length:
            context = context[:max_length] + "..."
        
        return f"\n\nRelevant Context:\n{context}\n"

