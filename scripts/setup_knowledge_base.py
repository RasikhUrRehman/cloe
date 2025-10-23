"""
Setup Knowledge Base
Initializes Milvus collection and ingests sample documents
"""
from ingestion import DocumentIngestion
from config import ensure_directories
from utils import setup_logging
import os

logger = setup_logging()


def setup_knowledge_base():
    """Set up the knowledge base with sample documents"""
    
    print("\n" + "="*60)
    print("CLEO KNOWLEDGE BASE SETUP")
    print("="*60 + "\n")
    
    # Ensure directories exist
    ensure_directories()
    
    # Initialize ingestion
    print("Connecting to Milvus...")
    try:
        ingestion = DocumentIngestion()
    except Exception as e:
        print(f"\n❌ Error: Could not connect to Milvus")
        print(f"   {str(e)}")
        print("\nMake sure Milvus is running:")
        print("   docker-compose up -d")
        return False
    
    print("✓ Connected to Milvus\n")
    
    # Create collection
    print("Creating/checking Milvus collection...")
    try:
        ingestion.create_collection(drop_existing=False)
        print("✓ Collection ready\n")
    except Exception as e:
        print(f"❌ Error creating collection: {e}")
        return False
    
    # Check for documents
    data_dir = "data/raw"
    if not os.path.exists(data_dir):
        print(f"❌ Directory not found: {data_dir}")
        print("\nCreate sample documents first:")
        print("   python create_sample_docs.py")
        return False
    
    pdf_files = [f for f in os.listdir(data_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {data_dir}")
        print("\nCreate sample documents first:")
        print("   python create_sample_docs.py")
        return False
    
    print(f"Found {len(pdf_files)} PDF file(s) to ingest:\n")
    for pdf in pdf_files:
        print(f"  • {pdf}")
    print()
    
    # Ingest documents
    results = []
    for pdf_file in pdf_files:
        pdf_path = os.path.join(data_dir, pdf_file)
        document_name = os.path.splitext(pdf_file)[0]
        
        # Determine job type and section from filename
        job_type = "warehouse"
        if "handbook" in pdf_file.lower():
            section = "company_info"
        elif "job" in pdf_file.lower() or "description" in pdf_file.lower():
            section = "job_requirements"
        else:
            section = "general"
        
        print(f"Ingesting: {pdf_file}")
        print(f"  Type: {job_type}, Section: {section}")
        
        try:
            result = ingestion.ingest_document(
                pdf_path=pdf_path,
                document_name=document_name,
                job_type=job_type,
                section=section
            )
            results.append(result)
            print(f"  ✓ Success: {result['total_chunks']} chunks indexed")
            print(f"  Total characters: {result['total_characters']}\n")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}\n")
            results.append({
                "document_name": document_name,
                "status": "failed",
                "error": str(e)
            })
    
    # Summary
    print("="*60)
    print("INGESTION SUMMARY")
    print("="*60 + "\n")
    
    successful = [r for r in results if r.get('status') == 'success']
    failed = [r for r in results if r.get('status') == 'failed']
    
    print(f"Total documents: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        total_chunks = sum(r.get('total_chunks', 0) for r in successful)
        print(f"Total chunks indexed: {total_chunks}")
    
    if failed:
        print("\nFailed documents:")
        for r in failed:
            print(f"  • {r['document_name']}: {r.get('error', 'Unknown error')}")
    
    print("\n" + "="*60)
    
    if successful:
        print("\n✓ Knowledge base setup complete!")
        print("\nYou can now:")
        print("  1. Test retrieval: python retrievers.py")
        print("  2. Run the agent: python main.py")
        print("  3. Run demo: python demo_conversation.py")
        return True
    else:
        print("\n❌ Knowledge base setup failed")
        return False


def test_retrieval():
    """Test the retrieval system"""
    from retrievers import KnowledgeBaseRetriever, RetrievalMethod
    
    print("\n" + "="*60)
    print("TESTING RETRIEVAL")
    print("="*60 + "\n")
    
    try:
        retriever = KnowledgeBaseRetriever()
        
        test_queries = [
            "What are the shift requirements?",
            "What are the job responsibilities?",
            "What benefits does the company offer?",
        ]
        
        for query in test_queries:
            print(f"Query: {query}")
            print("-" * 60)
            
            results = retriever.retrieve(
                query=query,
                method=RetrievalMethod.HYBRID,
                top_k=2
            )
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"\nResult {i}:")
                    print(f"  Document: {result['document_name']}")
                    print(f"  Section: {result['section']}")
                    print(f"  Score: {result.get('hybrid_score', result.get('score', 0)):.3f}")
                    print(f"  Text: {result['text'][:150]}...")
            else:
                print("  No results found")
            
            print("\n")
        
        print("="*60)
        print("✓ Retrieval test complete!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"❌ Retrieval test failed: {e}\n")


def main():
    """Main setup flow"""
    import sys
    
    # Check if sample docs should be created first
    if not os.path.exists("data/raw") or not any(f.endswith('.pdf') for f in os.listdir("data/raw")):
        print("\nNo PDF documents found.")
        response = input("Create sample documents? (yes/no): ").strip().lower()
        
        if response == 'yes':
            from create_sample_docs import main as create_docs
            create_docs()
        else:
            print("\nPlace PDF documents in data/raw/ directory and run this script again.")
            return
    
    # Setup knowledge base
    success = setup_knowledge_base()
    
    if success:
        # Ask if user wants to test retrieval
        response = input("\nTest retrieval system? (yes/no): ").strip().lower()
        if response == 'yes':
            test_retrieval()


if __name__ == "__main__":
    main()
