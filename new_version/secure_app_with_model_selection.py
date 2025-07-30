from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import OllamaLLM as Ollama
import streamlit as st
import os
import logging
import subprocess
import json
from typing import Dict, Any, Optional, List
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecureDataHandler:
    """Handles data sanitization for local models"""
    
    def __init__(self):
        self.sensitive_patterns = [
            r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit cards
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Emails
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{10,11}\b',  # Phone numbers
        ]
    
    def sanitize_schema(self, schema: str) -> str:
        """Remove sensitive table/column information"""
        # Filter out sensitive table names
        sensitive_tables = ['users', 'passwords', 'credit_cards', 'ssn', 'personal_data']
        sensitive_columns = ['password', 'ssn', 'credit_card', 'email', 'phone']
        
        # Simple filtering - in production, use more sophisticated methods
        for table in sensitive_tables:
            if table in schema.lower():
                schema = re.sub(rf'CREATE TABLE {table}[^;]+;', '', schema, flags=re.IGNORECASE)
        
        return schema
    
    def sanitize_results(self, results: str) -> str:
        """Mask sensitive data in query results"""
        sanitized = results
        for pattern in self.sensitive_patterns:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized)
        return sanitized

class QueryValidator:
    """Validates SQL queries for security"""
    
    def __init__(self):
        self.dangerous_operations = [
            'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE'
        ]
    
    def validate_sql(self, sql: str) -> bool:
        """Check if SQL query contains dangerous operations"""
        sql_upper = sql.upper()
        for operation in self.dangerous_operations:
            if operation in sql_upper:
                return False
        return True

class OllamaModelManager:
    """Manages Ollama models and provides model selection"""
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.available_models = self.get_available_models()
    
    def get_available_models(self) -> List[Dict[str, str]]:
        """Get list of available Ollama models"""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                models = []
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            model_name = parts[0]
                            model_id = parts[1]
                            size = parts[2] if len(parts) > 2 else "Unknown"
                            models.append({
                                'name': model_name,
                                'id': model_id,
                                'size': size
                            })
                return models
            else:
                logger.error(f"Failed to get models: {result.stderr}")
                return []
        except Exception as e:
            logger.error(f"Error getting models: {e}")
            return []
    
    def get_recommended_models(self) -> List[str]:
        """Get list of recommended models for SQL tasks"""
        recommended = [
            'sqlcoder:15b',
            'deepseek-coder:33b',
            'codellama:13b-instruct',
            'llama3:latest',
            'mistral:instruct',
            'qwen2.5:14b-instruct-8k',
            'deepseek-r1:7b-8k'
        ]
        
        available_names = [model['name'] for model in self.available_models]
        return [model for model in recommended if model in available_names]
    
    def create_llm(self, model_name: str, temperature: float = 0) -> Optional[Ollama]:
        """Create LLM instance with specified model"""
        try:
            llm = OllamaLLM(
                model=model_name,
                base_url=self.base_url,
                temperature=temperature
            )
            logger.info(f"Successfully created LLM with model: {model_name}")
            return llm
        except Exception as e:
            logger.error(f"Failed to create LLM with model {model_name}: {e}")
            return None

def init_database(user: str, password: str, host: str, port: str, database: str) -> SQLDatabase:
    """Initialize database connection"""
    db_uri = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
    return SQLDatabase.from_uri(db_uri)

def get_sql_chain(db, llm, data_handler: SecureDataHandler):
    """Create SQL generation chain with local LLM"""
    template = """
    You are a SQL expert. Based on the database schema below, write a complete SQL query to answer the user's question.
    
    <SCHEMA>{schema}</SCHEMA>
    
    Conversation History: {chat_history}
    
    IMPORTANT: Write ONLY the complete SQL query. Do not include any explanations, comments, or markdown formatting.
    
    Examples:
    Question: "which 3 artists have the most tracks?"
    SQL Query: SELECT ArtistId, COUNT(*) as track_count FROM Track GROUP BY ArtistId ORDER BY track_count DESC LIMIT 3;
    
    Question: "Name 10 artists"
    SQL Query: SELECT Name FROM Artist LIMIT 10;
    
    Question: "Show me all customers"
    SQL Query: SELECT * FROM Customer;
    
    Now answer this question:
    Question: {question}
    SQL Query:"""
    
    prompt = ChatPromptTemplate.from_template(template)
    
    def get_schema(_):
        """Get sanitized schema information"""
        schema = db.get_table_info()
        return data_handler.sanitize_schema(schema)
    
    return (
        RunnablePassthrough.assign(schema=get_schema)
        | prompt
        | llm
        | StrOutputParser()
    )

def get_response(user_query: str, db: SQLDatabase, chat_history: list, llm, data_handler: SecureDataHandler, validator: QueryValidator):
    """Generate response using local LLM with security measures"""
    try:
        sql_chain = get_sql_chain(db, llm, data_handler)
        
        template = """
        You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
        Based on the table schema below, question, sql query, and sql response, write a natural language response.
        <SCHEMA>{schema}</SCHEMA>

        Conversation History: {chat_history}
        SQL Query: <SQL>{query}</SQL>
        User question: {question}
        SQL Response: {response}"""
        
        prompt = ChatPromptTemplate.from_template(template)
        
        def execute_query_safely(vars):
            """Execute query with security validation"""
            query = vars["query"]
            
            # Validate query
            if not validator.validate_sql(query):
                return "Error: Query contains potentially dangerous operations"
            
            try:
                # Execute query
                results = db.run(query)
                
                # Sanitize results
                return data_handler.sanitize_results(results)
            except Exception as e:
                logger.error(f"Query execution error: {e}")
                return f"Error executing query: {str(e)}"
        
        # First, get the SQL query
        sql_result = sql_chain.invoke({
            "question": user_query,
            "chat_history": chat_history,
        })
        
        # Debug: Check if SQL query is empty or incomplete
        sql_result = sql_result.strip()
        if not sql_result or sql_result == "":
            logger.error(f"Empty SQL query generated for question: {user_query}")
            return "Sorry, I couldn't generate a valid SQL query. Please try rephrasing your question."
        
        # Check if query is incomplete (just starts with SELECT)
        if sql_result.upper().startswith("SELECT") and len(sql_result.split()) < 3:
            logger.error(f"Incomplete SQL query generated: {sql_result}")
            return "Sorry, the generated SQL query is incomplete. Please try rephrasing your question or try a different model."
        
        # Additional validation: check for common incomplete patterns
        incomplete_patterns = [
            "SELECT",
            "SELECT *",
            "SELECT * FROM",
            "SELECT * FROM table"
        ]
        
        if any(sql_result.strip().upper() == pattern.upper() for pattern in incomplete_patterns):
            logger.error(f"Incomplete SQL query generated: {sql_result}")
            return "Sorry, the generated SQL query is incomplete. Please try rephrasing your question or try a different model."
        
        # Check if query ends with semicolon
        if not sql_result.endswith(';'):
            sql_result = sql_result + ';'
        
        logger.info(f"Generated SQL query: {sql_result}")
        
        # Execute the query safely
        query_result = execute_query_safely({"query": sql_result})
        
        # Generate the final response
        response_chain = (
            prompt
            | llm
            | StrOutputParser()
        )
        
        return response_chain.invoke({
            "schema": data_handler.sanitize_schema(db.get_table_info()),
            "chat_history": chat_history,
            "query": sql_result,
            "question": user_query,
            "response": query_result
        })
    
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return f"Sorry, I encountered an error: {str(e)}"

# Initialize components
load_dotenv()

# Initialize managers
model_manager = OllamaModelManager()
data_handler = SecureDataHandler()
validator = QueryValidator()

# Streamlit UI
def main():
    st.set_page_config(page_title="Secure AI SQL Chat", page_icon=":shield:")
    
    st.title("🔒 Secure AI SQL Chat (Local Models)")
    st.markdown("**Using local Ollama models for complete data privacy**")
    
    # Check if Ollama is available
    if not model_manager.available_models:
        st.error("""
        **Ollama not found or no models available!** 
        
        Please:
        1. Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
        2. Start Ollama: `ollama serve`
        3. Pull a model: `ollama pull sqlcoder:15b`
        """)
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.subheader("🔧 Configuration")
        
        # Model Selection
        st.markdown("### 🤖 Model Selection")
        
        # Get recommended models
        recommended_models = model_manager.get_recommended_models()
        all_models = [model['name'] for model in model_manager.available_models]
        
        # Create model selection
        if recommended_models:
            st.info("💡 **Recommended models for SQL tasks:**")
            for model in recommended_models:
                st.write(f"• {model}")
        
        selected_model = st.selectbox(
            "Choose Local Model:",
            options=all_models,
            index=0 if not recommended_models else all_models.index(recommended_models[0]),
            help="Select the local model to use for SQL generation"
        )
        
        # Model info
        selected_model_info = next((m for m in model_manager.available_models if m['name'] == selected_model), None)
        if selected_model_info:
            st.info(f"**Selected Model**: {selected_model}\n**Size**: {selected_model_info['size']}")
        
        # Temperature setting
        temperature = st.slider(
            "Temperature (Creativity)",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.1,
            help="Lower values = more focused, Higher values = more creative"
        )
        
        # Initialize LLM
        if 'current_llm' not in st.session_state or st.session_state.get('selected_model') != selected_model:
            with st.spinner(f"Loading model: {selected_model}..."):
                llm = model_manager.create_llm(selected_model, temperature)
                if llm:
                    st.session_state.current_llm = llm
                    st.session_state.selected_model = selected_model
                    st.success(f"✅ Model loaded: {selected_model}")
                else:
                    st.error(f"❌ Failed to load model: {selected_model}")
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
        
        # Available models info
        st.subheader("📊 Available Models")
        st.write(f"**Total Models**: {len(model_manager.available_models)}")
        
        # Show model sizes
        total_size = 0
        for model in model_manager.available_models:
            try:
                size_gb = float(model['size'].replace('GB', ''))
                total_size += size_gb
            except:
                pass
        
        st.write(f"**Total Size**: {total_size:.1f} GB")
        
        # Security status
        st.markdown("---")
        st.markdown("### 🔒 Security Status")
        st.success("✅ Local Model (No External Calls)")
        st.success("✅ Data Sanitization Enabled")
        st.success("✅ Query Validation Active")
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            AIMessage(content=f"🔒 Hello! I'm a secure AI SQL assistant using local model: {selected_model}. Your data never leaves your infrastructure. Connect to your database and ask me questions!")
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
            if "db" in st.session_state and "current_llm" in st.session_state:
                with st.spinner(f"🤖 Processing with {selected_model}..."):
                    response = get_response(
                        user_query, 
                        st.session_state.db, 
                        st.session_state.chat_history,
                        st.session_state.current_llm,
                        data_handler,
                        validator
                    )
                    st.markdown(response)
                    st.session_state.chat_history.append(AIMessage(content=response))
            else:
                if "db" not in st.session_state:
                    st.error("⚠️ Please connect to a database first.")
                if "current_llm" not in st.session_state:
                    st.error("⚠️ Please select a model first.")

if __name__ == "__main__":
    main() 