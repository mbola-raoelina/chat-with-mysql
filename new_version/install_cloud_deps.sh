#!/bin/bash

# Install Cloud Dependencies for Secure AI SQL Chat
echo "Installing cloud dependencies..."

# Install required packages
pip install langchain-openai
pip install langchain-groq
pip install -r requirements_cloud.txt

echo "Cloud dependencies installed successfully!"
echo "You can now run: streamlit run secure_app_cloud_only.py" 