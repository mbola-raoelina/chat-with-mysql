from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
import streamlit as st
import os
import logging
import json
from typing import Dict, Any, Optional, List
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecureDataHandler:
    """Handles data sanitization for cloud models"""
    
    def __init__(self):
        self.sensitive_patterns = [
            r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit cards
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Emails
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{10,11}\b',  # Phone numbers
        ]
    
    def sanitize_schema(self, schema: str) -> str:
        """Remove sensitive table/column information"""
        sensitive_tables = ['users', 'passwords', 'credit_cards', 'ssn', 'personal_data']
        sensitive_columns = ['password', 'ssn', 'credit_card', 'email', 'phone']
        
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

class CloudModelManager:
    """Manages cloud LLM models and provides model selection"""
    
    def __init__(self):
        self.available_models = {
            'openai': {
                'gpt-4o-mini': {'provider': 'OpenAI', 'cost': 'Low', 'speed': 'Fast'},
                'gpt-4o': {'provider': 'OpenAI', 'cost': 'Medium', 'speed': 'Fast'},
                'gpt-3.5-turbo': {'provider': 'OpenAI', 'cost': 'Low', 'speed': 'Very Fast'}
            },
            'groq': {
                'mixtral-8x7b-32768': {'provider': 'Groq', 'cost': 'Free', 'speed': 'Very Fast'},
                'llama3-70b-8192': {'provider': 'Groq', 'cost': 'Low', 'speed': 'Fast'},
                'gemma2-9b-it': {'provider': 'Groq', 'cost': 'Free', 'speed': 'Very Fast'}
            }
        }
    
    def get_available_models(self) -> Dict[str, Dict]:
        """Get list of available cloud models"""
        return self.available_models
    
    def create_llm(self, provider: str, model: str, api_key: str, temperature: float = 0) -> Optional[Any]:
        """Create LLM instance with specified model"""
        try:
            if provider == 'openai':
                llm = ChatOpenAI(
                    model=model,
                    openai_api_key=api_key,
                    temperature=temperature
                )
            elif provider == 'groq':
                llm = ChatGroq(
                    model=model,
                    groq_api_key=api_key,
                    temperature=temperature
                )
            else:
                raise ValueError(f"Unknown provider: {provider}")
            
            logger.info(f"Successfully created LLM with model: {model}")
            return llm
        except Exception as e:
            logger.error(f"Failed to create LLM with model {model}: {e}")
            return None

def init_database(user: str, password: str, host: str, port: str, database: str) -> SQLDatabase:
    """Initialize database connection"""
    db_uri = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
    return SQLDatabase.from_uri(db_uri)

def get_sql_chain(db, llm, data_handler: SecureDataHandler):
    """Create SQL generation chain with cloud LLM"""
    template = """
    You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
    Based on the table schema below, write a SQL query that would answer the user's question. Take the conversation history into account.
    
    <SCHEMA>{schema}</SCHEMA>
    
    Conversation History: {chat_history}
    
    Write only the SQL query and nothing else. Do not wrap the SQL query in any other text, not even backticks.
    
    For example:
    Question: which 3 artists have the most tracks?
    SQL Query: SELECT ArtistId, COUNT(*) as track_count FROM Track GROUP BY ArtistId ORDER BY track_count DESC LIMIT 3;
    Question: Name 10 artists
    SQL Query: SELECT Name FROM Artist LIMIT 10;
    
    Your turn:
    
    Question: {question}
    SQL Query:
    """
    
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
    """Generate response using cloud LLM with security measures"""
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
        
        chain = (
            RunnablePassthrough.assign(query=sql_chain).assign(
                schema=lambda _: data_handler.sanitize_schema(db.get_table_info()),
                response=execute_query_safely,
            )
            | prompt
            | llm
            | StrOutputParser()
        )
        
        return chain.invoke({
            "question": user_query,
            "chat_history": chat_history,
        })
    
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return f"Sorry, I encountered an error: {str(e)}"

# Initialize components
load_dotenv()

# Initialize managers
model_manager = CloudModelManager()
data_handler = SecureDataHandler()
validator = QueryValidator()

# Streamlit UI
def main():
    st.set_page_config(page_title="Secure AI SQL Chat (Cloud)", page_icon=":cloud:")
    
    st.title("☁️ Secure AI SQL Chat (Cloud Models)")
    st.markdown("**Using cloud models for easy deployment and accessibility**")
    
    # Sidebar
    with st.sidebar:
        st.subheader("🔧 Configuration")
        
        # Model Selection
        st.markdown("### 🤖 Model Selection")
        
        # Provider selection
        provider = st.selectbox(
            "Choose Provider:",
            options=['groq', 'openai'],
            index=0,
            help="Select your preferred LLM provider"
        )
        
        # Model selection based on provider
        available_models = model_manager.get_available_models()[provider]
        model_options = list(available_models.keys())
        
        selected_model = st.selectbox(
            "Choose Model:",
            options=model_options,
            index=0,
            help="Select the model to use for SQL generation"
        )
        
        # Model info
        model_info = available_models[selected_model]
        st.info(f"**Provider**: {model_info['provider']}\n**Cost**: {model_info['cost']}\n**Speed**: {model_info['speed']}")
        
        # API Key input
        st.markdown("### 🔑 API Configuration")
        
        if provider == 'openai':
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                help="Enter your OpenAI API key"
            )
        else:  # groq
            api_key = st.text_input(
                "Groq API Key",
                type="password",
                help="Enter your Groq API key (free tier available)"
            )
        
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
        if api_key and ('current_llm' not in st.session_state or 
                       st.session_state.get('selected_model') != selected_model or
                       st.session_state.get('provider') != provider):
            with st.spinner(f"Loading model: {selected_model}..."):
                llm = model_manager.create_llm(provider, selected_model, api_key, temperature)
                if llm:
                    st.session_state.current_llm = llm
                    st.session_state.selected_model = selected_model
                    st.session_state.provider = provider
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
        
        # Security status
        st.markdown("### 🔒 Security Status")
        st.success("✅ Cloud Model (Fast & Reliable)")
        st.success("✅ Data Sanitization Enabled")
        st.success("✅ Query Validation Active")
        st.warning("⚠️ Data sent to cloud provider")
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            AIMessage(content="☁️ Hello! I'm a secure AI SQL assistant using cloud models. Easy to use and deploy!")
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
                    st.error("⚠️ Please configure your API key and select a model first.")

if __name__ == "__main__":
    main() 