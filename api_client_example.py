"""
Example client for interacting with Cleo API
Demonstrates how to use the API endpoints
"""
import requests
import time
from typing import Optional


class CleoAPIClient:
    """Client for interacting with Cleo RAG Agent API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the API client
        
        Args:
            base_url: Base URL of the Cleo API
        """
        self.base_url = base_url
        self.session_id: Optional[str] = None
    
    def health_check(self) -> dict:
        """Check if the API is healthy"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def create_session(
        self,
        retrieval_method: str = "hybrid",
        language: str = "en"
    ) -> dict:
        """
        Create a new conversation session
        
        Args:
            retrieval_method: Retrieval method (semantic, similarity, hybrid)
            language: Language code (en, es, etc.)
        
        Returns:
            Session creation response
        """
        response = requests.post(
            f"{self.base_url}/api/v1/session/create",
            json={
                "retrieval_method": retrieval_method,
                "language": language
            }
        )
        response.raise_for_status()
        data = response.json()
        self.session_id = data["session_id"]
        return data
    
    def send_message(self, message: str, session_id: Optional[str] = None) -> dict:
        """
        Send a message to the agent
        
        Args:
            message: User's message
            session_id: Session ID (uses self.session_id if not provided)
        
        Returns:
            Chat response
        """
        if not session_id:
            session_id = self.session_id
        
        if not session_id:
            raise ValueError("No session_id provided and no active session")
        
        response = requests.post(
            f"{self.base_url}/api/v1/chat",
            json={
                "session_id": session_id,
                "message": message
            }
        )
        response.raise_for_status()
        return response.json()
    
    def get_status(self, session_id: Optional[str] = None) -> dict:
        """
        Get session status
        
        Args:
            session_id: Session ID (uses self.session_id if not provided)
        
        Returns:
            Session status
        """
        if not session_id:
            session_id = self.session_id
        
        if not session_id:
            raise ValueError("No session_id provided and no active session")
        
        response = requests.get(
            f"{self.base_url}/api/v1/session/{session_id}/status"
        )
        response.raise_for_status()
        return response.json()
    
    def delete_session(self, session_id: Optional[str] = None) -> dict:
        """
        Delete a session
        
        Args:
            session_id: Session ID (uses self.session_id if not provided)
        
        Returns:
            Deletion confirmation
        """
        if not session_id:
            session_id = self.session_id
        
        if not session_id:
            raise ValueError("No session_id provided and no active session")
        
        response = requests.delete(
            f"{self.base_url}/api/v1/session/{session_id}"
        )
        response.raise_for_status()
        
        if session_id == self.session_id:
            self.session_id = None
        
        return response.json()
    
    def reset_session(self, session_id: Optional[str] = None) -> dict:
        """
        Reset a session's conversation memory
        
        Args:
            session_id: Session ID (uses self.session_id if not provided)
        
        Returns:
            Reset confirmation
        """
        if not session_id:
            session_id = self.session_id
        
        if not session_id:
            raise ValueError("No session_id provided and no active session")
        
        response = requests.post(
            f"{self.base_url}/api/v1/session/{session_id}/reset"
        )
        response.raise_for_status()
        return response.json()


def demo_conversation():
    """Demonstrate a complete conversation flow"""
    print("=" * 60)
    print("Cleo API Client Demo")
    print("=" * 60)
    
    # Initialize client
    client = CleoAPIClient()
    
    # Check health
    print("\n1. Checking API health...")
    health = client.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Version: {health['version']}")
    
    # Create session
    print("\n2. Creating new session...")
    session_data = client.create_session()
    print(f"   Session ID: {session_data['session_id']}")
    print(f"   Current Stage: {session_data['current_stage']}")
    
    # Conversation flow
    messages = [
        "Hi there!",
        "Yes, I'm ready to apply",
        "I'm 25 years old",
        "Yes, I'm authorized to work",
        "I prefer morning shifts",
        "I can start next Monday",
    ]
    
    print("\n3. Having a conversation...")
    for i, message in enumerate(messages, 1):
        print(f"\n   Message {i}/{len(messages)}")
        print(f"   You: {message}")
        
        response = client.send_message(message)
        print(f"   Cleo: {response['response'][:150]}...")
        print(f"   Stage: {response['current_stage']}")
        
        # Brief pause between messages
        time.sleep(1)
    
    # Check final status
    print("\n4. Checking session status...")
    status = client.get_status()
    print(f"   Session ID: {status['session_id']}")
    print(f"   Current Stage: {status['current_stage']}")
    print(f"   Engagement Complete: {status['engagement_complete']}")
    print(f"   Qualification Complete: {status['qualification_complete']}")
    
    # Clean up
    print("\n5. Cleaning up...")
    client.delete_session()
    print("   Session deleted successfully")
    
    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


def interactive_mode():
    """Interactive mode for testing the API"""
    print("=" * 60)
    print("Cleo API Client - Interactive Mode")
    print("=" * 60)
    print("\nCommands:")
    print("  'new' - Create new session")
    print("  'status' - Show session status")
    print("  'reset' - Reset current session")
    print("  'delete' - Delete current session")
    print("  'quit' - Exit")
    print("=" * 60 + "\n")
    
    client = CleoAPIClient()
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            elif user_input.lower() == 'new':
                data = client.create_session()
                print(f"\nCreated session: {data['session_id']}")
                print(f"Stage: {data['current_stage']}\n")
            
            elif user_input.lower() == 'status':
                status = client.get_status()
                print("\n=== Session Status ===")
                for key, value in status.items():
                    print(f"{key}: {value}")
                print()
            
            elif user_input.lower() == 'reset':
                result = client.reset_session()
                print(f"\n{result['message']}\n")
            
            elif user_input.lower() == 'delete':
                result = client.delete_session()
                print(f"\n{result['message']}\n")
            
            else:
                # Send message
                response = client.send_message(user_input)
                print(f"\nCleo: {response['response']}")
                print(f"[Stage: {response['current_stage']}]\n")
        
        except ValueError as e:
            print(f"\nError: {e}")
            print("Please create a session first with 'new'\n")
        
        except requests.exceptions.RequestException as e:
            print(f"\nAPI Error: {e}")
            print("Is the API server running? (python run_api.py)\n")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_conversation()
    else:
        interactive_mode()
