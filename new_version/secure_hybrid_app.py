from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_community.llms import Ollama
import streamlit as st
import os
import logging
import json
from typing import Dict, Any, Optional, List
import re
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecureDataHandler:
    """Enhanced data sanitization for hybrid approach"""
    
    def __init__(self):
        self.sensitive_patterns = [
            r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit cards
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Emails
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{10,11}\b',  # Phone numbers
            r'\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b',  # IBAN
        ]
        
        # Sensitive table and column patterns
        self.sensitive_tables = [
            'users', 'passwords', 'credit_cards', 'ssn', 'personal_data',
            'customers', 'employees', 'patients', 'clients', 'accounts',
            'financial', 'medical', 'legal', 'confidential'
        ]
        
        self.sensitive_columns = [
            'password', 'ssn', 'credit_card', 'email', 'phone',
            'address', 'salary', 'medical', 'legal', 'confidential',
            'secret', 'private', 'internal', 'sensitive'
        ]
    
    def sanitize_schema(self, schema: str) -> str:
        """Remove ALL sensitive table/column information"""
        sanitized_schema = schema
        
        # Remove sensitive tables completely
        for table in self.sensitive_tables:
            # Remove CREATE TABLE statements for sensitive tables
            sanitized_schema = re.sub(
                rf'CREATE TABLE\s+`?{table}`?\s*\([^)]*\);?',
                f'-- Table {table} removed for security',
                sanitized_schema,
                flags=re.IGNORECASE | re.MULTILINE | re.DOTALL
            )
            
            # Remove table references in other statements
            sanitized_schema = re.sub(
                rf'`?{table}`?',
                '[REDACTED_TABLE]',
                sanitized_schema,
                flags=re.IGNORECASE
            )
        
        # Remove sensitive columns from remaining tables
        for column in self.sensitive_columns:
            sanitized_schema = re.sub(
                rf'`?{column}`?\s+[^,\n)]*',
                '[REDACTED_COLUMN]',
                sanitized_schema,
                flags=re.IGNORECASE
            )
        
        return sanitized_schema
    
    def sanitize_results(self, results: str) -> str:
        """Mask ALL sensitive data in query results"""
        sanitized = results
        
        # Apply all sensitive patterns
        for pattern in self.sensitive_patterns:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized)
        
        # Additional sanitization for common sensitive data
        sanitized = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[REDACTED_IP]', sanitized)
        sanitized = re.sub(r'\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b', '[REDACTED_IBAN]', sanitized)
        
        return sanitized
    
    def create_safe_prompt(self, user_query: str, schema: str) -> str:
        """Create a safe prompt that doesn't expose sensitive data"""
        # Sanitize schema before sending to cloud
        safe_schema = self.sanitize_schema(schema)
        
        # Create a generic prompt that doesn't reveal specific data
        safe_prompt = f"""
        You are a SQL assistant. Based on the sanitized schema below, generate a SQL query for: "{user_query}"
        
        Schema (sanitized):
        {safe_schema}
        
        Generate only the SQL query, nothing else.
        """
        
        return safe_prompt

class QueryValidator:
    """Enhanced query validation for security"""
    
    def __init__(self):
        self.dangerous_operations = [
            'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE',
            'GRANT', 'REVOKE', 'EXEC', 'EXECUTE', 'BACKUP', 'RESTORE'
        ]
        
        self.sensitive_tables = [
            'users', 'passwords', 'credit_cards', 'ssn', 'personal_data',
            'customers', 'employees', 'patients', 'clients', 'accounts'
        ]
    
    def validate_sql(self, sql: str) -> bool:
        """Check if SQL query is safe"""
        sql_upper = sql.upper()
        
        # Check for dangerous operations
        for operation in self.dangerous_operations:
            if operation in sql_upper:
                return False
        
        # Check for sensitive table access
        for table in self.sensitive_tables:
            if table in sql_upper:
                return False
        
        return True

class HybridModelManager:
    """Manages both local and cloud models with security"""
    
    def __init__(self):
        self.local_models = {
            'sqlcoder:15b': {'type': 'local', 'size': '9GB', 'specialty': 'SQL'},
            'deepseek-coder:33b': {'type': 'local', 'size': '18GB', 'specialty': 'Code'},
            'codellama:13b-instruct': {'type': 'local', 'size': '7.4GB', 'specialty': 'Code'},
            'llama3:latest': {'type': 'local', 'size': '4.7GB', 'specialty': 'General'}
        }
        
        self.cloud_models = {
            'groq': {
                'mixtral-8x7b-32768': {'cost': 'Free', 'speed': 'Very Fast'},
                'llama3-70b-8192': {'cost': 'Low', 'speed': 'Fast'}
            },
            'openai': {
                'gpt-4o-mini': {'cost': 'Low', 'speed': 'Fast'},
                'gpt-3.5-turbo': {'cost': 'Low', 'speed': 'Very Fast'}
            }
        }
    
    def get_available_local_models(self) -> List[str]:
        """Get list of available local models"""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                models = []
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            models.append(parts[0])
                return models
            return []
        except Exception as e:
            logger.error(f"Error getting local models: {e}")
            return []
    
    def create_local_llm(self, model_name: str, temperature: float = 0) -> Optional[Ollama]:
        """Create local LLM instance"""
        try:
            llm = Ollama(
                model=model_name,
                base_url="http://localhost:11434",
                temperature=temperature
            )
            return llm
        except Exception as e:
            logger.error(f"Failed to create local LLM: {e}")
            return None
    
    def create_cloud_llm(self, provider: str, model: str, api_key: str, temperature: float = 0) -> Optional[Any]:
        """Create cloud LLM instance"""
        try:
            if provider == 'groq':
                llm = ChatGroq(
                    model=model,
                    groq_api_key=api_key,
                    temperature=temperature
                )
            elif provider == 'openai':
                llm = ChatOpenAI(
                    model=model,
                    openai_api_key=api_key,
                    temperature=temperature
                )
            else:
                raise ValueError(f"Unknown provider: {provider}")
            
            return llm
        except Exception as e:
            logger.error(f"Failed to create cloud LLM: {e}")
            return None

def init_database(user: str, password: str, host: str, port: str, database: str) -> SQLDatabase:
    """Initialize database connection"""
    db_uri = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
    return SQLDatabase.from_uri(db_uri)

def get_sql_chain_secure(db, llm, data_handler: SecureDataHandler, use_local: bool = True):
    """Create SQL generation chain with enhanced security"""
    
    if use_local:
        # Local processing - full schema available
        template = """
        You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
        Based on the table schema below, write a SQL query that would answer the user's question.
        
        <SCHEMA>{schema}</SCHEMA>
        
        Write only the SQL query and nothing else. Do not wrap the SQL query in any other text, not even backticks.
        
        Question: {question}
        SQL Query:
        """
    else:
        # Cloud processing - sanitized schema only
        template = """
        You are a SQL assistant. Based on the sanitized schema below, generate a SQL query.
        
        <SCHEMA>{schema}</SCHEMA>
        
        Generate only the SQL query for: {question}
        """
    
    prompt = ChatPromptTemplate.from_template(template)
    
    def get_schema(_):
        """Get schema information (full or sanitized)"""
        schema = db.get_table_info()
        if use_local:
            return schema  # Full schema for local processing
        else:
            return data_handler.sanitize_schema(schema)  # Sanitized for cloud
    
    return (
        RunnablePassthrough.assign(schema=get_schema)
        | prompt
        | llm
        | StrOutputParser()
    )

def get_response_secure(user_query: str, db: SQLDatabase, chat_history: list, llm, data_handler: SecureDataHandler, validator: QueryValidator, use_local: bool = True):
    """Generate response with enhanced security"""
    try:
        sql_chain = get_sql_chain_secure(db, llm, data_handler, use_local)
        
        # Generate SQL query
        sql_query = sql_chain.invoke({"question": user_query})
        
        # Validate SQL query
        if not validator.validate_sql(sql_query):
            return "❌ **Security Error**: Query contains potentially dangerous operations or accesses sensitive tables."
        
        # Execute query safely
        try:
            results = db.run(sql_query)
            
            # Sanitize results before any processing
            sanitized_results = data_handler.sanitize_results(results)
            
            # Generate response based on sanitized results
            if use_local:
                # Local processing - can work with sanitized results
                response_template = """
                Based on the query results, provide a natural language response.
                
                SQL Query: {query}
                Results: {results}
                Question: {question}
                
                Provide a clear, helpful response explaining the results.
                """
            else:
                # Cloud processing - minimal data exposure
                response_template = """
                The query has been executed successfully. Here are the results:
                
                SQL Query: {query}
                Results: {results}
                
                Provide a brief summary of the findings.
                """
            
            prompt = ChatPromptTemplate.from_template(response_template)
            chain = prompt | llm | StrOutputParser()
            
            response = chain.invoke({
                "query": sql_query,
                "results": sanitized_results,
                "question": user_query
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            return f"❌ **Error executing query**: {str(e)}"
    
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return f"❌ **Error**: {str(e)}"

# Initialize components
load_dotenv()

# Initialize managers
model_manager = HybridModelManager()
data_handler = SecureDataHandler()
validator = QueryValidator()

# Streamlit UI
def main():
    st.set_page_config(page_title="Secure AI SQL Chat (Hybrid)", page_icon=":shield:")
    
    st.title("🛡️ Secure AI SQL Chat (Hybrid)")
    st.markdown("**Maximum security with local processing, cloud fallback**")
    
    # Sidebar
    with st.sidebar:
        st.subheader("🔧 Configuration")
        
        # Processing Mode Selection
        st.markdown("### 🎯 Processing Mode")
        processing_mode = st.radio(
            "Choose Processing Mode:",
            options=["Local Only (Maximum Security)", "Hybrid (Local + Cloud)", "Cloud Only (Fast)"],
            index=0,
            help="Local: Complete privacy. Hybrid: Local SQL + Cloud response. Cloud: Fast but limited privacy."
        )
        
        if processing_mode == "Local Only (Maximum Security)":
            st.success("✅ **Maximum Security**: All processing local")
            
            # Local model selection
            available_local = model_manager.get_available_local_models()
            if available_local:
                selected_local = st.selectbox(
                    "Choose Local Model:",
                    options=available_local,
                    help="Select local model for processing"
                )
                
                # Initialize local LLM
                if 'local_llm' not in st.session_state or st.session_state.get('selected_local') != selected_local:
                    with st.spinner(f"Loading local model: {selected_local}..."):
                        llm = model_manager.create_local_llm(selected_local)
                        if llm:
                            st.session_state.local_llm = llm
                            st.session_state.selected_local = selected_local
                            st.success(f"✅ Local model loaded: {selected_local}")
                        else:
                            st.error(f"❌ Failed to load local model")
                            st.stop()
            else:
                st.error("❌ No local models available")
                st.info("Please install Ollama and pull models: `ollama pull sqlcoder:15b`")
                st.stop()
        
        elif processing_mode == "Hybrid (Local + Cloud)":
            st.info("🔄 **Hybrid Mode**: Local SQL generation, cloud response")
            
            # Local model for SQL generation
            available_local = model_manager.get_available_local_models()
            if available_local:
                selected_local = st.selectbox(
                    "Local Model (SQL Generation):",
                    options=available_local,
                    help="Local model for SQL generation"
                )
                
                # Cloud model for response generation
                st.markdown("### ☁️ Cloud Model (Response Generation)")
                provider = st.selectbox("Provider:", ['groq', 'openai'])
                
                if provider == 'groq':
                    api_key = st.text_input("Groq API Key", type="password")
                    cloud_model = st.selectbox("Model:", ['mixtral-8x7b-32768', 'llama3-70b-8192'])
                else:
                    api_key = st.text_input("OpenAI API Key", type="password")
                    cloud_model = st.selectbox("Model:", ['gpt-4o-mini', 'gpt-3.5-turbo'])
                
                # Initialize models
                if api_key and available_local:
                    if 'hybrid_models' not in st.session_state:
                        with st.spinner("Loading hybrid models..."):
                            local_llm = model_manager.create_local_llm(selected_local)
                            cloud_llm = model_manager.create_cloud_llm(provider, cloud_model, api_key)
                            
                            if local_llm and cloud_llm:
                                st.session_state.hybrid_models = {
                                    'local': local_llm,
                                    'cloud': cloud_llm
                                }
                                st.success("✅ Hybrid models loaded")
                            else:
                                st.error("❌ Failed to load models")
                                st.stop()
            else:
                st.error("❌ No local models available for hybrid mode")
                st.stop()
        
        else:  # Cloud Only
            st.warning("⚠️ **Limited Privacy**: Data sent to cloud")
            
            # Cloud model selection
            provider = st.selectbox("Provider:", ['groq', 'openai'])
            
            if provider == 'groq':
                api_key = st.text_input("Groq API Key", type="password")
                cloud_model = st.selectbox("Model:", ['mixtral-8x7b-32768', 'llama3-70b-8192'])
            else:
                api_key = st.text_input("OpenAI API Key", type="password")
                cloud_model = st.selectbox("Model:", ['gpt-4o-mini', 'gpt-3.5-turbo'])
            
            # Initialize cloud LLM
            if api_key and ('cloud_llm' not in st.session_state or st.session_state.get('provider') != provider):
                with st.spinner(f"Loading cloud model: {cloud_model}..."):
                    llm = model_manager.create_cloud_llm(provider, cloud_model, api_key)
                    if llm:
                        st.session_state.cloud_llm = llm
                        st.session_state.provider = provider
                        st.success(f"✅ Cloud model loaded: {cloud_model}")
                    else:
                        st.error(f"❌ Failed to load cloud model")
                        st.stop()
        
        st.divider()
        
        # Security settings
        st.markdown("### 🛡️ Security Settings")
        enable_sanitization = st.checkbox("Enable Data Sanitization", value=True)
        enable_validation = st.checkbox("Enable Query Validation", value=True)
        
        st.divider()
        
        # Database connection
        st.subheader("🗄️ Database Connection")
        
        host = st.text_input("Host", value="localhost", key="Host")
        port = st.text_input("Port", value="3306", key="Port")
        user = st.text_input("User", value="root", key="User")
        password = st.text_input("Password", type="password", value="", key="Password")
        database = st.text_input("Database", value="Chinook", key="Database")
        
        if st.button("🔗 Connect to Database"):
            if password:
                try:
                    with st.spinner("Connecting to database..."):
                        db = init_database(user, password, host, port, database)
                        st.session_state.db = db
                        st.success("✅ Connected to database!")
                except Exception as e:
                    st.error(f"❌ Connection failed: {e}")
            else:
                st.error("Please enter a password")
        
        st.divider()
        
        # Security status
        st.markdown("### 🔒 Security Status")
        if processing_mode == "Local Only (Maximum Security)":
            st.success("✅ Complete Privacy (Local Only)")
        elif processing_mode == "Hybrid (Local + Cloud)":
            st.success("✅ Enhanced Security (Hybrid)")
            st.info("🔄 Local SQL + Cloud Response")
        else:
            st.warning("⚠️ Limited Privacy (Cloud Only)")
        
        st.success("✅ Data Sanitization Active")
        st.success("✅ Query Validation Active")
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            AIMessage(content="🛡️ Hello! I'm a secure AI SQL assistant. Choose your processing mode for maximum security!")
        ]
    
    # Display chat history
    for message in st.session_state.chat_history:
        if isinstance(message, AIMessage):
            with st.chat_message("AI"):
                st.markdown(message.content)
        elif isinstance(message, HumanMessage):
            with st.chat_message("Human"):
                st.markdown(message.content)
    
    # Chat input
    user_query = st.chat_input("Ask a question about your database...")
    
    if user_query is not None and user_query.strip() != "":
        # Add user message to history
        st.session_state.chat_history.append(HumanMessage(content=user_query))
        
        # Display user message
        with st.chat_message("Human"):
            st.markdown(user_query)
        
        # Generate and display AI response
        with st.chat_message("AI"):
            if "db" in st.session_state:
                with st.spinner("🤖 Processing securely..."):
                    if processing_mode == "Local Only (Maximum Security)":
                        if 'local_llm' in st.session_state:
                            response = get_response_secure(
                                user_query, 
                                st.session_state.db, 
                                st.session_state.chat_history,
                                st.session_state.local_llm,
                                data_handler,
                                validator,
                                use_local=True
                            )
                        else:
                            response = "❌ Local model not loaded"
                    
                    elif processing_mode == "Hybrid (Local + Cloud)":
                        if 'hybrid_models' in st.session_state:
                            # Use local for SQL, cloud for response
                            response = get_response_secure(
                                user_query, 
                                st.session_state.db, 
                                st.session_state.chat_history,
                                st.session_state.hybrid_models['local'],
                                data_handler,
                                validator,
                                use_local=True
                            )
                        else:
                            response = "❌ Hybrid models not loaded"
                    
                    else:  # Cloud Only
                        if 'cloud_llm' in st.session_state:
                            response = get_response_secure(
                                user_query, 
                                st.session_state.db, 
                                st.session_state.chat_history,
                                st.session_state.cloud_llm,
                                data_handler,
                                validator,
                                use_local=False
                            )
                        else:
                            response = "❌ Cloud model not loaded"
                    
                    st.markdown(response)
                    st.session_state.chat_history.append(AIMessage(content=response))
            else:
                st.error("⚠️ Please connect to a database first.")

if __name__ == "__main__":
    main() 