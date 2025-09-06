#!/usr/bin/env python3
"""
🔍 Path Debugging Script
========================
This script helps identify where models are saved vs where the app looks for them.
"""

import os
from pathlib import Path
import sys

def debug_paths():
    """Debug all relevant paths"""
    print("🔍 PATH DEBUGGING REPORT")
    print("=" * 60)
    
    # Current working directory
    cwd = Path.cwd()
    print(f"📂 Current Working Directory: {cwd}")
    
    # Script location
    script_path = Path(__file__).resolve()
    print(f"📄 This Script Location: {script_path}")
    print(f"📁 This Script Parent: {script_path.parent}")
    
    # Check if we're in the right project structure
    print(f"\n🏗️ PROJECT STRUCTURE CHECK:")
    project_files = [
        "app/main.py",
        "scripts/model_training.py", 
        "data/parkinsons.csv",
        "scripts/models/",
        "models/"  # Alternative location
    ]
    
    for file_path in project_files:
        full_path = cwd / file_path
        exists = "✅" if full_path.exists() else "❌"
        print(f"   {exists} {file_path}: {full_path}")
    
    # Check for model files in different locations
    print(f"\n🤖 MODEL FILE LOCATIONS:")
    model_locations = [
        cwd / "scripts" / "models" / "parkinsons_model.pkl",
        cwd / "models" / "parkinsons_model.pkl", 
        cwd / "app" / "models" / "parkinsons_model.pkl",
        cwd / "parkinsons_model.pkl"
    ]
    
    for model_path in model_locations:
        exists = "✅" if model_path.exists() else "❌"
        print(f"   {exists} {model_path}")
    
    # Show what the training script would create
    print(f"\n📊 TRAINING SCRIPT PATHS:")
    if (cwd / "scripts" / "model_training.py").exists():
        # Simulate what the training script sees
        training_root = (cwd / "scripts" / "model_training.py").resolve().parent
        models_dir = training_root / "models"
        print(f"   📁 Training script ROOT: {training_root}")
        print(f"   📁 Models would be saved to: {models_dir}")
        
        if models_dir.exists():
            print(f"   📋 Files in models dir:")
            for file in models_dir.iterdir():
                print(f"      • {file.name}")
    
    # Show what the Streamlit app expects
    print(f"\n🚀 STREAMLIT APP EXPECTATIONS:")
    if (cwd / "app" / "main.py").exists():
        print(f"   📁 App location: {cwd / 'app' / 'main.py'}")
        print(f"   📁 App probably looks for models at:")
        
        # Common patterns for model loading in Streamlit apps
        possible_paths = [
            cwd / "models" / "parkinsons_model.pkl",
            cwd / "app" / "models" / "parkinsons_model.pkl",
            (cwd / "app").parent / "models" / "parkinsons_model.pkl",
            cwd / "scripts" / "models" / "parkinsons_model.pkl"
        ]
        
        for path in possible_paths:
            exists = "✅" if path.exists() else "❌"
            print(f"      {exists} {path}")
    
    # Python path info
    print(f"\n🐍 PYTHON ENVIRONMENT:")
    print(f"   📍 Python executable: {sys.executable}")
    print(f"   📍 Python path: {sys.path[0]}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if not (cwd / "data" / "parkinsons.csv").exists():
        print(f"   ❌ Missing dataset! Download from:")
        print(f"      https://archive.ics.uci.edu/ml/datasets/parkinsons")
        print(f"      Save as: {cwd / 'data' / 'parkinsons.csv'}")
    
    model_found = any(path.exists() for path in model_locations)
    if not model_found:
        print(f"   ❌ No model files found! Run training:")
        print(f"      cd {cwd}")
        print(f"      python scripts/model_training.py")
    else:
        print(f"   ✅ Model files exist, but may be in wrong location")
        print(f"      Check your Streamlit app's model loading path")
    
    print("=" * 60)

if __name__ == "__main__":
    debug_paths()