#!/usr/bin/env python3
"""
Fix CSV schema to match current Pydantic models
"""
import os
import shutil
from chatbot.state.states import StateManager, EngagementState, QualificationState, ApplicationState, VerificationState

def backup_and_recreate_csv():
    """Backup existing CSV files and recreate with proper schema"""
    storage_dir = "storage"
    backup_dir = "storage/backup"
    
    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)
    
    csv_files = [
        "engagement_states.csv",
        "qualification_states.csv", 
        "application_states.csv",
        "verification_states.csv",
        "sessions.csv"
    ]
    
    # Backup existing files
    for csv_file in csv_files:
        original_path = os.path.join(storage_dir, csv_file)
        backup_path = os.path.join(backup_dir, f"{csv_file}.backup")
        
        if os.path.exists(original_path):
            shutil.copy2(original_path, backup_path)
            print(f"Backed up {csv_file} to {backup_path}")
            
            # Remove original to force recreation with new schema
            os.remove(original_path)
            print(f"Removed {original_path} - will be recreated with new schema")
    
    # Initialize StateManager to recreate files with proper schema
    manager = StateManager()
    print("Recreated CSV files with proper schema")

if __name__ == "__main__":
    backup_and_recreate_csv()