# 🚀 Main Entry Point for Streamlit Cloud Deployment
# This file serves as the entry point for Streamlit Cloud

import streamlit as st
import sys
import os

# Add the new_version directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'new_version'))

# Import and run the cloud app
from secure_app_cloud_only import main

if __name__ == "__main__":
    main() 