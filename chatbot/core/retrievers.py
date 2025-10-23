"""
Retriever Methods Module
Implements semantic search, similarity search, and hybrid search
"""
from typing import List, Dict, Any, Optional
from enum import Enum
from langchain_openai import OpenAIEmbeddings
from pymilvus import Collection, connections
from config import settings
from utils import setup_logging

logger = setup_logging()


class RetrievalMethod(Enum):
    """Enumeration of available retrieval methods"""
    SEMANTIC = "semantic"
    SIMILARITY = "similarity"
    HYBRID = "hybrid"


class KnowledgeBaseRetriever:
    """Retrieves relevant information from Milvus vector store"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self._ensure_connection()
        self.collection = Collection(settings.MILVUS_COLLECTION_NAME)
        self.collection.load()
    
    def _ensure_connection(self):
        """Ensure Milvus connection is established"""
        try:
            connections.connect(
                alias="default",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT
            )
            logger.info("Connected to Milvus for retrieval")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise
    
    def _generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for query text"""
        embedding = self.embeddings.embed_query(query)
        return embedding
    
    def semantic_search(
        self,
        query: str,
        top_k: int = None,
        filters: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search using vector similarity
        
        Args:
            query: Search query text
            top_k: Number of results to return
            filters: Optional filters (e.g., {'job_type': 'healthcare'})
        
        Returns:
            List of relevant documents with scores
        """
        if top_k is None:
            top_k = settings.TOP_K_RESULTS
        
        logger.info(f"Performing semantic search for: '{query}'")
        
        # Generate query embedding
        query_embedding = self._generate_query_embedding(query)
        
        # Build filter expression
        filter_expr = None
        if filters:
            filter_parts = [f'{key} == "{value}"' for key, value in filters.items()]
            filter_expr = " && ".join(filter_parts)
        
        # Search parameters
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        # Perform search
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=filter_expr,
            output_fields=["text", "document_name", "job_type", "section", "chunk_index"]
        )
        
        # Format results
        formatted_results = []
        for hits in results:
            for hit in hits:
                formatted_results.append({
                    "text": hit.entity.get("text"),
                    "document_name": hit.entity.get("document_name"),
                    "job_type": hit.entity.get("job_type"),
                    "section": hit.entity.get("section"),
                    "chunk_index": hit.entity.get("chunk_index"),
                    "score": hit.score,
                    "distance": hit.distance
                })
        
        logger.info(f"Found {len(formatted_results)} results")
        return formatted_results
    
    def similarity_search(
        self,
        query: str,
        top_k: int = None,
        threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Similarity search with threshold filtering
        
        Args:
            query: Search query text
            top_k: Number of results to return
            threshold: Minimum similarity score threshold
        
        Returns:
            List of relevant documents above threshold
        """
        if top_k is None:
            top_k = settings.TOP_K_RESULTS
        if threshold is None:
            threshold = settings.SIMILARITY_THRESHOLD
        
        logger.info(f"Performing similarity search with threshold {threshold}")
        
        # Perform semantic search first
        results = self.semantic_search(query, top_k=top_k * 2)
        
        # Filter by threshold
        filtered_results = [
            result for result in results
            if result["score"] >= threshold
        ][:top_k]
        
        logger.info(f"Filtered to {len(filtered_results)} results above threshold")
        return filtered_results
    
    def hybrid_search(
        self,
        query: str,
        top_k: int = None,
        semantic_weight: float = 0.6,
        keyword_weight: float = 0.4
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic and keyword matching
        
        Args:
            query: Search query text
            top_k: Number of results to return
            semantic_weight: Weight for semantic similarity (0-1)
            keyword_weight: Weight for keyword matching (0-1)
        
        Returns:
            List of relevant documents with combined scores
        """
        if top_k is None:
            top_k = settings.TOP_K_RESULTS
        
        logger.info(f"Performing hybrid search")
        
        # Get semantic search results
        semantic_results = self.semantic_search(query, top_k=top_k * 2)
        
        # Calculate keyword match scores
        query_keywords = set(query.lower().split())
        
        for result in semantic_results:
            text_keywords = set(result["text"].lower().split())
            keyword_overlap = len(query_keywords & text_keywords)
            keyword_score = keyword_overlap / max(len(query_keywords), 1)
            
            # Combine scores
            result["keyword_score"] = keyword_score
            result["semantic_score"] = result["score"]
            result["hybrid_score"] = (
                semantic_weight * result["semantic_score"] +
                keyword_weight * keyword_score
            )
        
        # Sort by hybrid score and take top_k
        hybrid_results = sorted(
            semantic_results,
            key=lambda x: x["hybrid_score"],
            reverse=True
        )[:top_k]
        
        logger.info(f"Hybrid search returned {len(hybrid_results)} results")
        return hybrid_results
    
    def retrieve(
        self,
        query: str,
        method: RetrievalMethod = RetrievalMethod.HYBRID,
        top_k: int = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Main retrieval method that routes to specific search type
        
        Args:
            query: Search query text
            method: Retrieval method to use
            top_k: Number of results to return
            **kwargs: Additional arguments for specific methods
        
        Returns:
            List of relevant documents
        """
        if method == RetrievalMethod.SEMANTIC:
            return self.semantic_search(query, top_k=top_k, **kwargs)
        elif method == RetrievalMethod.SIMILARITY:
            return self.similarity_search(query, top_k=top_k, **kwargs)
        elif method == RetrievalMethod.HYBRID:
            return self.hybrid_search(query, top_k=top_k, **kwargs)
        else:
            raise ValueError(f"Unknown retrieval method: {method}")
    
    def format_context(self, results: List[Dict[str, Any]]) -> str:
        """
        Format retrieval results into context string for LLM
        
        Args:
            results: List of retrieval results
        
        Returns:
            Formatted context string
        """
        if not results:
            return "No relevant information found in the knowledge base."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[Source {i}] (Document: {result['document_name']}, "
                f"Section: {result['section']}, Score: {result.get('score', 0):.3f})\n"
                f"{result['text']}\n"
            )
        
        return "\n".join(context_parts)


def main():
    """Example usage of retriever"""
    retriever = KnowledgeBaseRetriever()
    
    # Example: Semantic search
    query = "What are the shift requirements for warehouse positions?"
    results = retriever.retrieve(
        query=query,
        method=RetrievalMethod.SEMANTIC,
        top_k=3
    )
    
    print(f"\n=== Semantic Search Results ===")
    for i, result in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"  Document: {result['document_name']}")
        print(f"  Section: {result['section']}")
        print(f"  Score: {result['score']:.3f}")
        print(f"  Text: {result['text'][:200]}...")
    
    # Example: Format context
    context = retriever.format_context(results)
    print(f"\n=== Formatted Context ===\n{context}")


if __name__ == "__main__":
    main()
