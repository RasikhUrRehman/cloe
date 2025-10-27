"""
Simple LangFuse connection test
"""
import os
from dotenv import load_dotenv

load_dotenv()

def test_langfuse_connection():
    """Test LangFuse API connection"""
    
    secret_key = os.getenv('LANGFUSE_SECRET_KEY')
    public_key = os.getenv('LANGFUSE_PUBLIC_KEY') 
    host = os.getenv('LANGFUSE_HOST')
    
    print("🔐 Testing LangFuse Connection")
    print("=" * 40)
    print(f"Secret Key: {secret_key[:10]}...{secret_key[-4:]}" if secret_key else "❌ No Secret Key")
    print(f"Public Key: {public_key[:10]}...{public_key[-4:]}" if public_key else "❌ No Public Key")
    print(f"Host: {host}")
    print()
    
    try:
        from langfuse import Langfuse
        
        # Test connection
        langfuse = Langfuse(
            secret_key=secret_key,
            public_key=public_key,
            host=host
        )
        
        # Try to create a simple trace
        trace = langfuse.trace(name="connection_test")
        print("✅ Successfully connected to LangFuse!")
        print(f"📊 Trace created: {trace.id}")
        
        # Test if we can flush data
        langfuse.flush()
        print("✅ Successfully flushed data to LangFuse!")
        
        return True
        
    except Exception as e:
        print(f"❌ LangFuse connection failed: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check your API keys are correct")
        print("2. Verify your LangFuse project is active")
        print("3. Check if you're using the right region (EU vs US)")
        print("4. Try regenerating your API keys")
        return False

if __name__ == "__main__":
    test_langfuse_connection()