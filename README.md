# 🛡️ Secure AI SQL Chat

**A privacy-focused SQL chat application with local models for maximum security.**

## 🚀 Quick Start

### **Option 1: Cloud Models (Recommended) - Best Performance**
```bash
# 1. Install dependencies
.\new_version\install_cloud_deps.ps1  # Windows
./new_version/install_cloud_deps.sh   # Linux/Mac

# 2. Get free API key from Groq: https://console.groq.com/
# 3. Run the app
streamlit run new_version/secure_app_cloud_only.py
# 4. Enter API key in sidebar
```

### **Option 2: Local Models (Maximum Security)**
```bash
# 1. Install Ollama: https://ollama.ai/download
# 2. Download models
.\new_version\setup_models.ps1  # Windows
./new_version/setup_models.sh   # Linux/Mac
# 3. Run the app
streamlit run new_version/secure_app_with_model_selection.py
```

### **Option 3: Hybrid Approach (Balanced)**
```bash
streamlit run new_version/secure_hybrid_app.py
```

## 🤖 **AI System Architecture & Data Flow**

### **📊 System Overview Diagram**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SECURE AI SQL CHAT SYSTEM                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   USER INPUT    │───▶│  STREAMLIT UI   │───▶│  AI PROCESSING  │
│  (Natural Lang) │    │   (Frontend)    │    │   (Backend)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  DATABASE       │◀───│  SECURITY       │◀───│  LLM MODELS     │
│  (MySQL)        │    │  LAYER          │    │  (Groq/OpenAI)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **🔄 Detailed AI Processing Flow**

#### **Step 1: User Input Processing**
```
User Question: "Show me top 5 customers by sales"
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    INPUT VALIDATION                        │
│  • Check for dangerous keywords (DROP, DELETE, etc.)      │
│  • Validate natural language format                        │
│  • Sanitize user input                                    │
└─────────────────────────────────────────────────────────────┘
```

#### **Step 2: Database Schema Retrieval**
```
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                SCHEMA SANITIZATION                         │
│  • Connect to MySQL database                              │
│  • Extract table structures                               │
│  • Remove sensitive tables/columns                        │
│  • Format schema for AI consumption                       │
└─────────────────────────────────────────────────────────────┘
```

#### **Step 3: AI SQL Generation**
```
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                LLM SQL GENERATION                          │
│  • Send to Cloud LLM (Groq/OpenAI)                       │
│  • Include: Schema + User Question + Chat History         │
│  • Generate SQL query using AI model                      │
│  • Validate SQL syntax and security                       │
└─────────────────────────────────────────────────────────────┘
```

#### **Step 4: Query Execution & Security**
```
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                QUERY EXECUTION                             │
│  • Execute SQL against MySQL database                     │
│  • Capture query results                                  │
│  • Sanitize sensitive data in results                     │
│  • Handle errors gracefully                               │
└─────────────────────────────────────────────────────────────┘
```

#### **Step 5: AI Response Generation**
```
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│              NATURAL LANGUAGE RESPONSE                     │
│  • Send results back to LLM                               │
│  • Generate human-readable explanation                    │
│  • Include: Query + Results + Context                     │
│  • Format response for user display                       │
└─────────────────────────────────────────────────────────────┘
```

### **🔐 Security Features Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SECURITY LAYERS                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  INPUT          │───▶│  QUERY          │───▶│  OUTPUT         │
│  SANITIZATION   │    │  VALIDATION     │    │  SANITIZATION   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  • Remove       │    │  • Block DROP   │    │  • Mask emails  │
│    sensitive    │    │  • Block DELETE │    │  • Mask SSNs    │
│    keywords     │    │  • Block ALTER  │    │  • Mask phones  │
│  • Validate     │    │  • Block CREATE │    │  • Mask cards   │
│    input format │    │  • Allow SELECT │    │  • Format data  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **🤖 AI Model Integration**

#### **Cloud Models (Recommended)**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CLOUD AI MODELS                                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     GROQ        │    │    OPENAI       │    │   HYBRID        │
│   (Free Tier)   │    │  (Pay-per-use)  │    │   (Combined)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  • mixtral-8x7b │    │  • gpt-4o-mini  │    │  • SQL: Local   │
│  • llama3-70b   │    │  • gpt-4o       │    │  • Response:    │
│  • gemma2-9b    │    │  • gpt-3.5-turbo│    │    Cloud        │
│  • 100 req/min  │    │  • Variable cost │    │  • Balanced     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### **Local Models (Maximum Security)**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LOCAL AI MODELS                                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   OLLAMA        │    │   SQLCODER      │    │   DEEPSEEK      │
│   (Local)       │    │   (SQL-focused) │    │   (Code-focused)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  • llama3:latest│    │  • sqlcoder:15b │    │  • deepseek-coder│
│  • 4.7GB RAM    │    │  • 9GB RAM      │    │  • 18GB RAM     │
│  • Offline      │    │  • SQL-optimized│    │  • Code-optimized│
│  • Free         │    │  • Free         │    │  • Free         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **📊 Data Flow Diagram**

```
USER QUESTION
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AI PROCESSING PIPELINE                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   INPUT     │─▶│   SCHEMA    │─▶│   SQL GEN   │─▶│   QUERY     │
│ SANITIZATION│  │ EXTRACTION  │  │   (LLM)     │  │ EXECUTION   │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
       │               │               │               │
       ▼               ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ • Remove    │  │ • Connect   │  │ • Send to   │  │ • Execute   │
│   sensitive │  │   to MySQL  │  │   Cloud LLM │  │   against   │
│   keywords  │  │ • Get table │  │ • Generate  │  │   database  │
│ • Validate  │  │   structure │  │   SQL query │  │ • Capture   │
│   format    │  │ • Sanitize  │  │ • Validate  │  │   results   │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
                                                           │
                                                           ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   RESPONSE  │◀─│   OUTPUT    │◀─│   NATURAL   │◀─│   RESULT    │
│ GENERATION  │  │ SANITIZATION│  │  LANGUAGE   │  │ PROCESSING  │
│   (LLM)     │  │             │  │  GENERATION │  │             │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
       │               │               │               │
       ▼               ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ • Send to   │  │ • Mask      │  │ • Send to   │  │ • Sanitize  │
│   Cloud LLM │  │   sensitive │  │   Cloud LLM │  │   data      │
│ • Generate  │  │   data      │  │ • Generate  │  │ • Format    │
│   response  │  │ • Format    │  │   human-    │  │   results   │
│ • Display   │  │   output    │  │   readable  │  │ • Handle    │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```

### **🔧 Key AI Components**

#### **1. Natural Language Processing**
- **Input**: User questions in natural language
- **Processing**: AI understands intent and context
- **Output**: Structured SQL query requirements

#### **2. SQL Generation**
- **Input**: Database schema + user question + chat history
- **Processing**: AI generates syntactically correct SQL
- **Output**: Executable SQL query

#### **3. Query Execution**
- **Input**: Generated SQL query
- **Processing**: Execute against MySQL database
- **Output**: Raw query results

#### **4. Response Generation**
- **Input**: SQL query + results + original question
- **Processing**: AI explains results in natural language
- **Output**: Human-readable response

### **🛡️ Security Implementation**

#### **Data Privacy Protection**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SECURITY MEASURES                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  SCHEMA         │    │  QUERY          │    │  RESULTS        │
│  FILTERING      │    │  VALIDATION     │    │  SANITIZATION   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  • Remove       │    │  • Block        │    │  • Mask emails  │
│    sensitive    │    │    dangerous     │    │  • Mask SSNs    │
│    tables       │    │    operations    │    │  • Mask phones  │
│  • Filter       │    │  • Allow only   │    │  • Mask cards   │
│    columns      │    │    SELECT       │    │  • Format data  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 Model Requirements

### **Local Models (Optional):**
- **sqlcoder:15b** (~9GB): SQL-optimized model
- **deepseek-coder:33b** (~18GB): Code generation model  
- **codellama:13b-instruct** (~7.4GB): General coding model
- **llama3:latest** (~4.7GB): General purpose model

### **Cloud Models (Free):**
- **Groq**: Free tier available (100 requests/minute)
- **OpenAI**: Pay-per-use

## 🔒 Security Features

### **🛡️ Data Privacy:**
- **Local Processing**: No data sent to cloud providers
- **Schema Privacy**: Database structure never exposed
- **Query Privacy**: SQL generation happens locally
- **Result Privacy**: Sensitive data masked before processing

### **🔐 Security Measures:**
- **Data Sanitization**: Mask sensitive patterns (SSN, credit cards, emails)
- **Query Validation**: Block dangerous operations (DROP, DELETE, etc.)
- **Access Control**: Prevent access to sensitive tables
- **Audit Logging**: Track all AI-generated queries

## 📊 Deployment Options

| Aspect | Local-Only | Hybrid | Cloud-Only |
|--------|------------|--------|------------|
| **Schema Privacy** | ✅ Complete | ✅ Complete | ❌ Exposed |
| **Query Privacy** | ✅ Complete | ✅ Complete | ❌ Exposed |
| **Result Privacy** | ✅ Complete | ✅ Sanitized | ⚠️ Sanitized |
| **Compliance** | ✅ Full | ✅ Enhanced | ❌ Limited |
| **Setup Complexity** | ❌ High | ⚠️ Medium | ✅ Low |
| **Performance** | ⚠️ Medium | ✅ Good | ✅ Fast |
| **Cost** | ✅ Free | ⚠️ Low | ❌ Variable |

## 🏗️ Project Structure

```
chat-with-mysql/
├── 📄 README.md                           # This file
├── 📄 requirements.txt                     # Dependencies
├── 📄 .gitignore                          # Excludes models
├── 📄 streamlit_app.py                    # Cloud deployment entry
├── 📁 new_version/
│   ├── 📄 secure_app_with_model_selection.py    # Local models
│   ├── 📄 secure_hybrid_app.py                 # Hybrid approach
│   ├── 📄 secure_app_cloud_only.py             # Cloud models
│   ├── 📄 setup_models.ps1                     # Windows setup
│   ├── 📄 setup_models.sh                      # Linux/Mac setup
│   ├── 📄 requirements_secure.txt              # Local deps
│   └── 📄 requirements_cloud.txt               # Cloud deps
├── 📁 docs/
│   └── 📄 architecture_diagram.md             # System architecture
└── 📁 old_version/                         # Original implementation
```

## 🔧 Installation

### **Prerequisites:**
- Python 3.8+
- MySQL database
- Ollama (for local models)
- 8GB+ RAM (for local models)

### **Step 1: Install Dependencies**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### **Step 2: Configure Database**
```bash
# Create .env file
echo "DB_HOST=localhost" > .env
echo "DB_PORT=3306" >> .env
echo "DB_USER=root" >> .env
echo "DB_PASSWORD=your_password" >> .env
echo "DB_NAME=your_database" >> .env
```

### **Step 3: Set Up Models**
```bash
# For Local Models:
.\new_version\setup_models.ps1  # Windows
./new_version/setup_models.sh   # Linux/Mac

# For Cloud Models:
# Get free API key from Groq: https://console.groq.com/
```

### **Step 4: Run Application**
```bash
# Cloud models (recommended - best performance)
streamlit run new_version/secure_app_cloud_only.py

# Local models (maximum security)
streamlit run new_version/secure_app_with_model_selection.py

# Hybrid approach
streamlit run new_version/secure_hybrid_app.py
```

## 🎯 Usage Examples

### **Example 1: Basic Query**
```
User: "Show me all customers"
AI: "SELECT * FROM customers;"
```

### **Example 2: Complex Analysis**
```
User: "What are the top 5 products by sales in the last month?"
AI: "SELECT p.product_name, SUM(od.quantity * od.unit_price) as total_sales 
     FROM products p 
     JOIN order_details od ON p.product_id = od.product_id 
     JOIN orders o ON od.order_id = o.order_id 
     WHERE o.order_date >= DATE_SUB(NOW(), INTERVAL 1 MONTH) 
     GROUP BY p.product_id 
     ORDER BY total_sales DESC 
     LIMIT 5;"
```

## 🚀 Deployment

### **For GitHub/Streamlit Cloud:**
```bash
# Push to GitHub (models excluded automatically)
git add .
git commit -m "Initial commit: Secure AI SQL Chat"
git push origin main

# Deploy to Streamlit Cloud
# 1. Go to https://share.streamlit.io/
# 2. Connect your GitHub repository
# 3. Set deployment path to streamlit_app.py
# 4. Deploy!
```

### **For Cloud Deployment (Recommended):**
```bash
# Run with cloud models (best performance)
streamlit run new_version/secure_app_cloud_only.py
```

### **For Local Deployment:**
```bash
# Run with local models
streamlit run new_version/secure_app_with_model_selection.py
```

## 🆘 Support

### **Common Issues:**

#### **"Ollama not found"**
```bash
# Install Ollama: https://ollama.ai/download
# Restart terminal after installation
```

#### **"No models available"**
```bash
# Run setup script
.\new_version\setup_models.ps1  # Windows
./new_version/setup_models.sh   # Linux/Mac
```

#### **"Database connection failed"**
```bash
# Check MySQL is running
# Verify credentials in .env file
# Test connection manually
```

#### **"API key error"**
```bash
# Get free API key from: https://console.groq.com/
# Enter key in app sidebar
```

---

**🛡️ Remember: When it comes to database security, it's better to be overly cautious than to risk exposing sensitive information to third-party providers.**

**Happy secure SQL chatting!** 🚀 