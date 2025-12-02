"""
Main Application Entry Point
Initializes Cleo RAG Agent and provides command-line interface
"""
import sys
import os
from typing import Optional

# Add chatbot package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatbot.core.agent import CleoRAGAgent
from chatbot.state.states import SessionState, ConversationStage
from chatbot.utils.report_generator import ReportGenerator
from chatbot.utils.config import ensure_directories
from chatbot.utils.utils import setup_logging

logger = setup_logging()


class CleoApplication:
    """Main application class for Cleo RAG Agent"""

    def __init__(self):
        """Initialize the Cleo application"""
        ensure_directories()
        self.agent: Optional[CleoRAGAgent] = None
        self.report_generator = ReportGenerator()

    def start_new_session(self) -> str:
        """
        Start a new conversation session

        Returns:
            Session ID
        """
        logger.info("Starting new session")

        # Create new agent
        self.agent = CleoRAGAgent()

        session_id = self.agent.session_state.session_id
        logger.info(f"Created new session: {session_id}")

        return session_id

    def resume_session(self, session_id: str) -> bool:
        """
        Resume an existing conversation session - Not supported with in-memory storage

        Args:
            session_id: Session ID to resume

        Returns:
            False - session resumption not supported
        """
        logger.warning(f"Session resumption not supported: {session_id}")
        return False

    def chat(self, message: str) -> str:
        """
        Send a message to the agent and get response

        Args:
            message: User's message

        Returns:
            Agent's response (if multiple messages, they are joined with newlines)
        """
        if not self.agent:
            return "Please start a new session first."

        # Process message returns a list of messages
        responses = self.agent.process_message(message)

        # Join multiple messages with double newline for readability
        return "\n\n".join(responses)

    def get_session_summary(self) -> dict:
        """Get summary of current session"""
        if not self.agent:
            return {"error": "No active session"}

        return self.agent.get_conversation_summary()

    def generate_report(self, include_fit_score: bool = False) -> dict:
        """
        Generate eligibility report for current session

        Args:
            include_fit_score: Whether to include fit score in report

        Returns:
            Dictionary with report paths
        """
        if not self.agent:
            return {"error": "No active session"}

        session_id = self.agent.session_state.session_id
        return self.report_generator.generate_report(
            session_id=session_id,
            include_fit_score=include_fit_score
        )

    def run_interactive(self):
        """Run interactive command-line interface"""
        print("=" * 60)
        print("Welcome to Cleo - Your AI Job Application Assistant")
        print("=" * 60)
        print("\nCommands:")
        print("  'new' - Start a new session")
        print("  'resume <session_id>' - Resume an existing session")
        print("  'summary' - Show session summary")
        print("  'report' - Generate eligibility report")
        print("  'quit' - Exit application")
        print("\n" + "=" * 60 + "\n")

        while True:
            try:
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nThank you for using Cleo!")
                    break

                elif user_input.lower() == 'new':
                    session_id = self.start_new_session()
                    print(f"\nStarted new session: {session_id}")
                    print("You can now start chatting!\n")
                    continue

                elif user_input.lower().startswith('resume '):
                    session_id = user_input[7:].strip()
                    if self.resume_session(session_id):
                        print(f"\nResumed session: {session_id}")
                        summary = self.get_session_summary()
                        print(f"Current stage: {summary['current_stage']}\n")
                    else:
                        print(f"\nCould not find session: {session_id}\n")
                    continue

                elif user_input.lower() == 'summary':
                    summary = self.get_session_summary()
                    print("\n=== Session Summary ===")
                    for key, value in summary.items():
                        print(f"{key}: {value}")
                    print()
                    continue

                elif user_input.lower() == 'report':
                    print("\nGenerating report...")
                    result = self.generate_report(include_fit_score=True)
                    if 'error' in result:
                        print(f"Error: {result['error']}\n")
                    else:
                        print(f"Report generated successfully!")
                        print(f"JSON: {result['json_report']}")
                        print(f"PDF: {result['pdf_report']}\n")
                    continue

                # Regular chat message
                response = self.chat(user_input)
                print(f"\nCleo: {response}\n")

                # Show current stage
                if self.agent:
                    summary = self.get_session_summary()
                    print(f"[Stage: {summary['current_stage']}]\n")

            except KeyboardInterrupt:
                print("\n\nThank you for using Cleo!")
                break
            except Exception as e:
                logger.error(f"Error in interactive mode: {e}")
                print(f"\nAn error occurred: {e}\n")


def main():
    """Main entry point"""
    app = CleoApplication()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'new':
            session_id = app.start_new_session()
            print(f"Started new session: {session_id}")

        elif command == 'resume' and len(sys.argv) > 2:
            session_id = sys.argv[2]
            if app.resume_session(session_id):
                print(f"Resumed session: {session_id}")
            else:
                print(f"Could not find session: {session_id}")

        else:
            print("Usage:")
            print("  python main.py              - Run interactive mode")
            print("  python main.py new          - Start new session")
            print("  python main.py resume <id>  - Resume session")
            print("\nFor API mode, run: python run_api.py")
    else:
        # Run interactive mode
        app.run_interactive()


if __name__ == "__main__":
    main()
