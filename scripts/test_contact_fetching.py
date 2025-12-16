import os
from typing import Optional
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor, BaseSingleActionAgent
from dataclasses import dataclass, field
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Dummy classes to simulate your existing structure
@dataclass
class Engagement:
    xano_session_id: Optional[str] = "dummy_session_123"

@dataclass
class ApplicationState:
    session_id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None

@dataclass
class SessionState:
    session_id: str = "test_session_001"
    engagement: Optional[Engagement] = field(default_factory=lambda: Engagement())
    application: Optional[ApplicationState] = None

@dataclass  
class XanoClient:
    """Dummy Xano client for testing"""
    def get_messages_by_session_id(self, session_id: str):
        # Return dummy conversation with contact info
        return [
            {"MsgCreator": "user", "MsgContent": "Hi, "},
            {"MsgCreator": "assistant", "MsgContent": "hi there what is your name? email and phone"},
            {"MsgCreator": "user", "MsgContent": "my name is beheeek smith"},
            {"MsgCreator": "user", "MsgContent": "mikaal.ahmad@example.com and phone is 555123-4567"},
            {"MsgCreator": "assistant", "MsgContent": "Got it, thanks for sharing your contact info."}
        ]

class DummyAgent:
    def __init__(self):
        # Create a simple memory with sample conversation
        self.memory = ConversationBufferMemory(return_messages=True)
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.0,
            openai_api_key=os.getenv("OPENAI_API_KEY", "dummy-key")
        )
        
        # Add some conversation to memory
        self.memory.chat_memory.add_user_message("Hi, ")
        self.memory.chat_memory.add_ai_message("hi there what is your name? email and phone")
        self.memory.chat_memory.add_user_message("my name is beheeek smith")
        self.memory.chat_memory.add_user_message("mikaal.ahmad@example.com and phone is 555123-4567")
        self.memory.chat_memory.add_ai_message("Got it, thanks for sharing your contact info.")

class ContactInfoExtractor:
    def __init__(self):
        # Set up session state
        self.session_state = SessionState()
        self.session_state.application = ApplicationState(session_id=self.session_state.session_id)
        
        # Create agent with memory
        self.agent = DummyAgent()
        
        # Initialize Xano client (dummy)
        self.xano_client = XanoClient()
        
        # Import your function (would normally be imported from your module)
        # For this example, we'll include it in the class
        self._fetch_contact_info_from_memory = self._create_fetch_method()
    
    def _create_fetch_method(self):
        """Create the _fetch_contact_info_from_memory method for this class"""
        # This is essentially your existing function as a method
        # (You would normally import this from your module)
        import json
        import re
        import logging
        from langchain.chat_models import ChatOpenAI
        
        logger = logging.getLogger(__name__)
        print("Setting up contact info extraction method...")
        
        def _fetch_contact_info_from_memory():
            """Your existing function as a method"""
            try:
                # Build transcript from agent memory
                transcript = []
                if self.agent and hasattr(self.agent, 'memory') and hasattr(self.agent.memory, 'chat_memory'):
                    mem = self.agent.memory.chat_memory
                    for m in mem.messages:
                        role = getattr(m, 'type', 'human')
                        content = getattr(m, 'content', '') or ''
                        transcript.append(f"{role}: {content}")
                
                if not transcript:
                    return False
                
                # Use LLM to extract contact info
                llm = self.agent.llm
                
                transcript_text = "\n".join(transcript)
                prompt = (
                    "You are a strict JSON extractor. Given the following conversation transcript between an agent and a user, extract the candidate's full name, email address, and phone number. \n"
                    "IMPORTANT INSTRUCTIONS:\n"
                    "- full_name: Extract BOTH first name AND last name. If only one name is mentioned, then ask to give full name. And judge with NER that it is a name and then store.\n"
                    "- email: Extract the complete email address with proper format (username@domain.extension). Skip if format is invalid.\n"
                    "- phone: Extract the phone number with all digits.\n"
                    "Return ONLY valid JSON with the exact keys: full_name, email, phone. Use null for missing fields and don't output any other text. If multiple values are present, use the most recent values.\n"
                    "Examples:\n"
                    "- Good full_name: \"John Smith\", \"Sarah Johnson\"\n"
                    "- Incomplete full_name: \"John\" (only first name)\n"
                    "- Good email: \"john.smith@gmail.com\", \"sarah@company.co.uk\"\n"
                    "- Invalid email: \"john@test\" (missing extension), \"test@test\" (incomplete domain)\n\n"
                    f"TRANSCRIPT:\n{transcript_text}\n\n"
                )
                
                print("Calling LLM to extract contact info from transcript")
                response = llm.invoke(prompt)
                response_text = response.content
                
                # Extract JSON payload from response
                json_text = response_text.strip()
                if "```json" in json_text:
                    start = json_text.find('```json') + 7
                    end = json_text.find('```', start)
                    json_text = json_text[start:end].strip()
                elif "```" in json_text:
                    start = json_text.find('```') + 3
                    end = json_text.find('```', start)
                    json_text = json_text[start:end].strip()
                
                extracted = None
                try:
                    extracted = json.loads(json_text)
                    print(f"Extracted JSON: {extracted}")
                except Exception:
                    # Fallback regex extraction
                    extracted = {"full_name": None, "email": None, "phone": None}
                    email_m = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", response_text)
                    phone_m = re.search(r"(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})", response_text)
                    name_m = re.search(r"\"?full_name\"?\s*[:=]\s*\"([A-Za-z\s]+)\"", response_text)
                    if email_m:
                        extracted['email'] = email_m.group()
                    if phone_m:
                        extracted['phone'] = phone_m.group()
                    if name_m:
                        extracted['full_name'] = name_m.group(1).strip().title()
                
                # Update application state
                app = self.session_state.application
                updated = False
                if isinstance(extracted, dict):
                    f = extracted.get('full_name')
                    e = extracted.get('email')
                    p = extracted.get('phone')
                    
                    # Validate and save full name
                    if f and not app.full_name:
                        name_cleaned = f.strip().title()
                        name_parts = name_cleaned.split()
                        if len(name_parts) >= 2:
                            app.full_name = name_cleaned
                            updated = True
                    
                    # Validate and save email
                    if e and not app.email:
                        email_cleaned = e.strip().lower()
                        email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$"
                        if re.match(email_pattern, email_cleaned):
                            app.email = email_cleaned
                            updated = True
                    
                    # Save phone
                    if p and not app.phone_number:
                        app.phone_number = p.strip()
                        updated = True
                
                return updated
            except Exception as e:
                logger.error(f"Error while extracting contact info using LLM: {e}")
                return False
        
        return _fetch_contact_info_from_memory
    
    def extract_and_print_contact_info(self):
        """Call the extraction function and display results"""
        print("=" * 50)
        print("Extracting contact information from conversation memory...")
        print("=" * 50)
        
        # Call the extraction function
        success = self._fetch_contact_info_from_memory()
        
        if success:
            print("✅ Successfully extracted contact information!")
            print(f"Full Name: {self.session_state.application.full_name}")
            print(f"Email: {self.session_state.application.email}")
            print(f"Phone: {self.session_state.application.phone_number}")
        else:
            print("❌ Failed to extract contact information")
        
        return success

# Alternative: Simpler test function if you want to test just the extraction
def test_contact_extraction():
    """Simple test function to demonstrate calling the extraction"""
    
    # Set up environment (if using real OpenAI API)
    # os.environ["OPENAI_API_KEY"] = "your-api-key-here"
    
    # Create the extractor
    extractor = ContactInfoExtractor()
    
    # Call the extraction
    print("Starting contact info extraction test...\n")
    
    # Method 1: Using the class method
    result = extractor.extract_and_print_contact_info()
    
    # Method 2: Direct call (if you have access to the method)
    # result = extractor._fetch_contact_info_from_memory()
    
    return result

if __name__ == "__main__":
    # Run the test
    test_contact_extraction()