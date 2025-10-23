"""
Quick Start Script for Cleo RAG Agent
Automates the initial setup process
"""
import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def print_step(step_num, total_steps, description):
    """Print step information"""
    print(f"\n[Step {step_num}/{total_steps}] {description}")
    print("-" * 70)


def check_command(command):
    """Check if a command exists"""
    try:
        subprocess.run([command, "--version"], 
                      capture_output=True, 
                      shell=True, 
                      check=True)
        return True
    except:
        return False


def run_command(command, description, shell=True):
    """Run a command and show output"""
    print(f"\n  Running: {description}")
    print(f"  Command: {command}\n")
    try:
        result = subprocess.run(command, shell=shell, check=True)
        print(f"  ✓ Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed: {e}")
        return False


def check_prerequisites():
    """Check if prerequisites are installed"""
    print_step(1, 7, "Checking Prerequisites")
    
    prerequisites = {
        'python': 'Python 3.11+',
        'docker': 'Docker',
        'docker-compose': 'Docker Compose',
    }
    
    missing = []
    for cmd, name in prerequisites.items():
        if check_command(cmd):
            print(f"  ✓ {name} found")
        else:
            print(f"  ✗ {name} NOT found")
            missing.append(name)
    
    if missing:
        print(f"\n  ⚠ Missing prerequisites: {', '.join(missing)}")
        print(f"  Please install them before continuing.")
        return False
    
    print(f"\n  ✓ All prerequisites found!")
    return True


def setup_environment():
    """Set up environment file"""
    print_step(2, 7, "Setting Up Environment")
    
    if os.path.exists('.env'):
        print("  .env file already exists")
        response = input("  Overwrite? (yes/no): ").strip().lower()
        if response != 'yes':
            print("  Using existing .env file")
            return True
    
    if not os.path.exists('.env.example'):
        print("  ✗ .env.example not found")
        return False
    
    # Copy .env.example to .env
    try:
        with open('.env.example', 'r') as f:
            content = f.read()
        
        with open('.env', 'w') as f:
            f.write(content)
        
        print("  ✓ Created .env file from template")
        
        # Prompt for OpenAI API key
        print("\n  Enter your OpenAI API key:")
        api_key = input("  > ").strip()
        
        if api_key:
            with open('.env', 'r') as f:
                content = f.read()
            
            content = content.replace('your_openai_api_key_here', api_key)
            
            with open('.env', 'w') as f:
                f.write(content)
            
            print("  ✓ Updated .env with API key")
        else:
            print("  ⚠ No API key provided. Please edit .env manually.")
        
        return True
    
    except Exception as e:
        print(f"  ✗ Error creating .env: {e}")
        return False


def create_virtual_environment():
    """Create Python virtual environment"""
    print_step(3, 7, "Creating Virtual Environment")
    
    if os.path.exists('venv'):
        print("  Virtual environment already exists")
        return True
    
    return run_command(
        'python -m venv venv',
        'Creating virtual environment'
    )


def install_dependencies():
    """Install Python dependencies"""
    print_step(4, 7, "Installing Dependencies")
    
    # Determine pip command based on platform
    if sys.platform == 'win32':
        pip_cmd = '.\\venv\\Scripts\\pip.exe'
    else:
        pip_cmd = './venv/bin/pip'
    
    return run_command(
        f'{pip_cmd} install -r requirements.txt',
        'Installing Python packages'
    )


def start_milvus():
    """Start Milvus stack"""
    print_step(5, 7, "Starting Milvus Stack")
    
    print("  Starting Milvus, etcd, and MinIO...")
    return run_command(
        'docker-compose up -d',
        'Starting Docker containers'
    )


def create_sample_documents():
    """Create sample documents"""
    print_step(6, 7, "Creating Sample Documents")
    
    # Determine python command
    if sys.platform == 'win32':
        python_cmd = '.\\venv\\Scripts\\python.exe'
    else:
        python_cmd = './venv/bin/python'
    
    return run_command(
        f'{python_cmd} create_sample_docs.py',
        'Creating sample company documents'
    )


def setup_knowledge_base():
    """Setup knowledge base"""
    print_step(7, 7, "Setting Up Knowledge Base")
    
    # Determine python command
    if sys.platform == 'win32':
        python_cmd = '.\\venv\\Scripts\\python.exe'
    else:
        python_cmd = './venv/bin/python'
    
    print("  This will ingest sample documents into Milvus...")
    print("  (This may take a minute)")
    
    return run_command(
        f'{python_cmd} setup_knowledge_base.py',
        'Ingesting documents into knowledge base'
    )


def show_next_steps():
    """Show next steps"""
    print_header("Setup Complete! 🎉")
    
    # Determine python command
    if sys.platform == 'win32':
        python_cmd = '.\\venv\\Scripts\\python.exe'
        activate_cmd = '.\\venv\\Scripts\\Activate.ps1'
    else:
        python_cmd = './venv/bin/python'
        activate_cmd = 'source venv/bin/activate'
    
    print("Next Steps:")
    print(f"\n1. Activate virtual environment:")
    print(f"   {activate_cmd}")
    
    print(f"\n2. Run the demo conversation:")
    print(f"   {python_cmd} demo_conversation.py")
    
    print(f"\n3. Or start interactive mode:")
    print(f"   {python_cmd} main.py")
    
    print("\n" + "="*70)
    print("\nUseful Commands:")
    print(f"  • Test retrievers:  {python_cmd} retrievers.py")
    print(f"  • Test fit score:   {python_cmd} fit_score.py")
    print(f"  • Generate report:  {python_cmd} report_generator.py")
    print(f"  • Mock verification: {python_cmd} verification.py")
    
    print("\n" + "="*70)
    print("\nDocker Commands:")
    print("  • View logs:        docker-compose logs -f")
    print("  • Stop services:    docker-compose down")
    print("  • Restart services: docker-compose restart")
    
    print("\n" + "="*70)
    print("\nDocumentation:")
    print("  See README.md for detailed information")
    print("\n" + "="*70 + "\n")


def main():
    """Main setup flow"""
    print_header("Cleo RAG Agent - Quick Start Setup")
    
    print("This script will:")
    print("  1. Check prerequisites (Python, Docker)")
    print("  2. Set up environment variables")
    print("  3. Create virtual environment")
    print("  4. Install dependencies")
    print("  5. Start Milvus stack")
    print("  6. Create sample documents")
    print("  7. Setup knowledge base")
    
    response = input("\nContinue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("\nSetup cancelled.")
        return
    
    # Run setup steps
    steps = [
        check_prerequisites,
        setup_environment,
        create_virtual_environment,
        install_dependencies,
        start_milvus,
        create_sample_documents,
        setup_knowledge_base,
    ]
    
    for step in steps:
        if not step():
            print("\n" + "="*70)
            print("  ✗ Setup failed at step: " + step.__name__)
            print("="*70 + "\n")
            return
    
    # Show next steps
    show_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nSetup failed with error: {e}")
        sys.exit(1)
