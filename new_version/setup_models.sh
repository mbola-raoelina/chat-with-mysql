#!/bin/bash

# 🚀 Ollama Model Setup Script for Linux/Mac
# This script downloads the recommended models for the Secure AI SQL Chat application

echo "🛡️ Secure AI SQL Chat - Model Setup"
echo "====================================="

# Check if Ollama is installed
echo ""
echo "🔍 Checking if Ollama is installed..."
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found!"
    echo ""
    echo "📥 Please install Ollama first:"
    echo "   Visit: https://ollama.ai/download"
    echo "   Or run: curl -fsSL https://ollama.ai/install.sh | sh"
    echo ""
    echo "💡 After installation, restart your terminal and run this script again."
    exit 1
fi

echo "✅ Ollama found!"

# Check if Ollama service is running
echo ""
echo "🔍 Checking if Ollama service is running..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama service is running!"
else
    echo "⚠️ Ollama service not running. Starting Ollama..."
    ollama serve > /dev/null 2>&1 &
    sleep 10
    
    # Check again
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama service started successfully!"
    else
        echo "❌ Failed to start Ollama service!"
        echo "💡 Please start Ollama manually: ollama serve"
        exit 1
    fi
fi

# Define recommended models
declare -A models=(
    ["sqlcoder:15b"]="SQL-optimized model (~9GB)"
    ["deepseek-coder:33b"]="Code generation model (~18GB)"
    ["codellama:13b-instruct"]="General coding model (~7.4GB)"
    ["llama3:latest"]="General purpose model (~4.7GB)"
)

# Check existing models
echo ""
echo "📋 Checking existing models..."
existing_models=$(curl -s http://localhost:11434/api/tags | jq -r '.models[].name' 2>/dev/null || echo "")

if [ -n "$existing_models" ]; then
    echo "✅ Found existing models: $existing_models"
else
    echo "ℹ️ No existing models found."
fi

# Download missing models
echo ""
echo "📥 Downloading recommended models..."
total_models=${#models[@]}
downloaded_count=0

for model in "${!models[@]}"; do
    description="${models[$model]}"
    
    if echo "$existing_models" | grep -q "$model"; then
        echo "✅ $model already installed"
        ((downloaded_count++))
    else
        echo ""
        echo "📥 Downloading $model ($description)..."
        echo "⏳ This may take 5-30 minutes depending on your internet speed..."
        
        if ollama pull "$model"; then
            echo "✅ $model downloaded successfully!"
            ((downloaded_count++))
        else
            echo "❌ Failed to download $model"
        fi
    fi
done

# Summary
echo ""
echo "📊 Download Summary:"
echo "=================="
echo "Total recommended models: $total_models"
echo "Successfully downloaded: $downloaded_count"
echo "Already installed: $((total_models - downloaded_count))"

if [ $downloaded_count -eq $total_models ]; then
    echo ""
    echo "🎉 All models are ready!"
    echo "🚀 You can now run the Secure AI SQL Chat application:"
    echo "   streamlit run secure_app_with_model_selection.py"
else
    echo ""
    echo "⚠️ Some models failed to download."
    echo "💡 You can still run the app with available models."
    echo "💡 To retry downloading, run: ollama pull model_name"
fi

echo ""
echo "📚 For more information, see the documentation in the project folder."
echo "🛡️ Happy secure SQL chatting!" 