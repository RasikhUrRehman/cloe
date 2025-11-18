"""
Document Ingestion and Embedding Module
Handles PDF extraction, text chunking, and embedding generation
"""

import os
from typing import Any, Dict, List

import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from chatbot.utils.config import settings
from chatbot.utils.utils import setup_logging

logger = setup_logging()


class DocumentIngestion:
    """Handles document processing and vector storage"""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self._connect_milvus()

    def _connect_milvus(self):
        """Establish connection to Milvus"""
        try:
            connections.connect(
                alias="default", host=settings.MILVUS_HOST, port=settings.MILVUS_PORT
            )
            logger.info(
                f"Connected to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}"
            )
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise

    def create_collection(self, drop_existing: bool = False):
        """Create Milvus collection for storing embeddings"""
        collection_name = settings.MILVUS_COLLECTION_NAME

        # Drop existing collection if requested
        if drop_existing and utility.has_collection(collection_name):
            utility.drop_collection(collection_name)
            logger.info(f"Dropped existing collection: {collection_name}")

        # Check if collection already exists
        if utility.has_collection(collection_name):
            logger.info(f"Collection '{collection_name}' already exists")
            return Collection(collection_name)

        # Define schema
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=settings.EMBEDDING_DIMENSION,
            ),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="document_name", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="job_type", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="section", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
        ]

        schema = CollectionSchema(
            fields=fields, description="Cleo Knowledge Base Collection"
        )

        # Create collection
        collection = Collection(name=collection_name, schema=schema)

        # Create index for vector search
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128},
        }
        collection.create_index(field_name="embedding", index_params=index_params)

        logger.info(f"Created collection: {collection_name}")
        return collection

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using PyMuPDF"""
        try:
            doc = fitz.open(pdf_path)
            text = ""

            for page_num in range(len(doc)):
                page = doc[page_num]
                text += page.get_text()

            doc.close()
            logger.info(f"Extracted text from {pdf_path}: {len(text)} characters")
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            raise

    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks using LangChain splitter"""
        chunks = self.text_splitter.split_text(text)
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks using OpenAI"""
        try:
            embeddings = self.embeddings.embed_documents(texts)
            logger.info(f"Generated embeddings for {len(texts)} chunks")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def ingest_document(
        self,
        pdf_path: str,
        document_name: str,
        job_type: str = "general",
        section: str = "general",
    ) -> Dict[str, Any]:
        """
        Complete ingestion pipeline: extract, chunk, embed, and store

        Args:
            pdf_path: Path to the PDF document
            document_name: Name identifier for the document
            job_type: Type of job (e.g., healthcare, warehouse, retail)
            section: Section of document (e.g., requirements, benefits, company_info)

        Returns:
            Dictionary with ingestion statistics
        """
        logger.info(f"Starting ingestion for: {document_name}")

        # Validate PDF file exists
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Extract text
        text = self.extract_text_from_pdf(pdf_path)

        if not text.strip():
            raise ValueError(f"No text extracted from PDF: {pdf_path}")

        # Chunk text
        chunks = self.chunk_text(text)

        if not chunks:
            raise ValueError(f"No text chunks generated from PDF: {pdf_path}")

        # Generate embeddings
        embeddings = self.generate_embeddings(chunks)

        # Prepare data for insertion
        collection = Collection(settings.MILVUS_COLLECTION_NAME)

        data = [
            embeddings,  # embedding vectors
            chunks,  # text content
            [document_name] * len(chunks),  # document name
            [job_type] * len(chunks),  # job type
            [section] * len(chunks),  # section
            list(range(len(chunks))),  # chunk indices
        ]

        # Insert into Milvus
        collection.insert(data)
        collection.flush()

        logger.info(f"Inserted {len(chunks)} chunks into Milvus")

        return {
            "document_name": document_name,
            "job_type": job_type,
            "section": section,
            "total_chunks": len(chunks),
            "total_characters": len(text),
            "status": "success",
        }

    def get_document_stats(self, document_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific document in the knowledge base

        Args:
            document_name: Name of the document

        Returns:
            Document statistics
        """
        try:
            collection = Collection(settings.MILVUS_COLLECTION_NAME)
            collection.load()

            # Query for chunks of this document
            expr = f'document_name == "{document_name}"'
            results = collection.query(
                expr=expr, output_fields=["text", "job_type", "section", "chunk_index"]
            )

            if not results:
                return {"found": False, "message": "Document not found"}

            total_chars = sum(len(result["text"]) for result in results)
            job_types = set(result["job_type"] for result in results)
            sections = set(result["section"] for result in results)

            return {
                "found": True,
                "document_name": document_name,
                "total_chunks": len(results),
                "total_characters": total_chars,
                "job_types": list(job_types),
                "sections": list(sections),
            }

        except Exception as e:
            logger.error(f"Error getting document stats: {e}")
            return {"found": False, "error": str(e)}

    def ingest_directory(
        self, directory_path: str, job_type: str = "general", section: str = "general"
    ) -> List[Dict[str, Any]]:
        """
        Ingest all PDF files from a directory

        Args:
            directory_path: Path to directory containing PDFs
            job_type: Type of job for all documents
            section: Section for all documents

        Returns:
            List of ingestion results
        """
        results = []

        if not os.path.exists(directory_path):
            logger.error(f"Directory not found: {directory_path}")
            return results

        pdf_files = [f for f in os.listdir(directory_path) if f.endswith(".pdf")]

        logger.info(f"Found {len(pdf_files)} PDF files in {directory_path}")

        for pdf_file in pdf_files:
            pdf_path = os.path.join(directory_path, pdf_file)
            document_name = os.path.splitext(pdf_file)[0]

            try:
                result = self.ingest_document(
                    pdf_path=pdf_path,
                    document_name=document_name,
                    job_type=job_type,
                    section=section,
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to ingest {pdf_file}: {e}")
                results.append(
                    {
                        "document_name": document_name,
                        "status": "failed",
                        "error": str(e),
                    }
                )

        return results


def main():
    """Example usage of document ingestion"""
    from chatbot.utils.config import ensure_directories

    # Ensure directories exist
    ensure_directories()

    # Initialize ingestion
    ingestion = DocumentIngestion()

    # Create collection
    ingestion.create_collection(drop_existing=False)

    # Example: Ingest a single document
    result = ingestion.ingest_document(
        pdf_path="data/raw/example.pdf",
        document_name="company_handbook",
        job_type="general",
        section="company_info",
    )
    print(result)

    # Example: Ingest entire directory
    # results = ingestion.ingest_directory(
    #     directory_path="data/raw",
    #     job_type="warehouse",
    #     section="job_requirements"
    # )
    # print(f"Ingested {len(results)} documents")


if __name__ == "__main__":
    main()
