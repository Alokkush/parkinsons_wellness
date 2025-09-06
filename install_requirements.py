#!/usr/bin/env python3
"""
📦 Requirements Checker and Installer
====================================
Checks for and installs required packages for the Parkinson's ML project.
"""

import subprocess
import sys
import importlib

def check_and_install_package(package_name, import_name=None):
    """Check if a package is installed and install if missing"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name} is already installed")
        return True
    except ImportError:
        print(f"❌ {package_name} is missing, installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"✅ {package_name} installed successfully")
            return True
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package_name}")
            return False

def main():
    """Check and install all required packages"""
    print("📦 Checking and Installing Requirements...")
    print("=" * 50)
    
    # Core required packages
    required_packages = [
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("scikit-learn", "sklearn"),
        ("joblib", "joblib"),
        ("matplotlib", "matplotlib"),
        ("seaborn", "seaborn")
    ]
    
    # Optional packages (nice to have but not critical)
    optional_packages = [
        ("xgboost", "xgboost"),
        ("lightgbm", "lightgbm"),
        ("shap", "shap")
    ]
    
    print("\n🔧 Installing Core Packages:")
    core_success = True
    for package_name, import_name in required_packages:
        if not check_and_install_package(package_name, import_name):
            core_success = False
    
    print("\n🎁 Installing Optional Packages (for enhanced features):")
    for package_name, import_name in optional_packages:
        check_and_install_package(package_name, import_name)
    
    print("\n" + "=" * 50)
    if core_success:
        print("✅ Core requirements satisfied! Ready to run training.")
        print("\n🚀 Next steps:")
        print("   python scripts/model_training.py")
    else:
        print("❌ Some core packages failed to install.")
        print("💡 Try installing manually:")
        print("   pip install pandas numpy scikit-learn joblib matplotlib seaborn")
    print("=" * 50)

if __name__ == "__main__":
    main()