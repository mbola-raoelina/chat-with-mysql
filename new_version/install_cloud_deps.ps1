# Install Cloud Dependencies for Secure AI SQL Chat
Write-Host "Installing cloud dependencies..." -ForegroundColor Green

# Install required packages
pip install langchain-openai
pip install langchain-groq
pip install -r requirements_cloud.txt

Write-Host "Cloud dependencies installed successfully!" -ForegroundColor Green
Write-Host "You can now run: streamlit run secure_app_cloud_only.py" -ForegroundColor Yellow 