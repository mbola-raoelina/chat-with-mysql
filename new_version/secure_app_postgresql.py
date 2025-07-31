import streamlit as st
import os
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain.prompts import ChatPromptTemplate
import logging
from datetime import datetime
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Secure AI SQL Chat - PostgreSQL",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

class SecureDataHandler:
    """Handles data sanitization and security"""
    
    @staticmethod
    def sanitize_schema(schema_info):
        """Remove sensitive information from schema"""
        sensitive_patterns = [
            r'password', r'passwd', r'pwd',
            r'credit_card', r'cc_number', r'card_number',
            r'ssn', r'social_security',
            r'email', r'phone', r'telephone',
            r'address', r'street', r'city',
            r'ip_address', r'ip_addr',
            r'iban', r'account_number'
        ]
        
        sanitized = schema_info
        for pattern in sensitive_patterns:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    @staticmethod
    def sanitize_query_result(result):
        """Sanitize query results to remove sensitive data"""
        if not result:
            return result
            
        # Mask sensitive patterns in results
        sensitive_patterns = {
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': '[EMAIL]',
            r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b': '[CREDIT_CARD]',
            r'\b\d{3}-\d{2}-\d{4}\b': '[SSN]',
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b': '[IP_ADDRESS]'
        }
        
        sanitized = str(result)
        for pattern, replacement in sensitive_patterns.items():
            sanitized = re.sub(pattern, replacement, sanitized)
        
        return sanitized

class QueryValidator:
    """Validates SQL queries for security"""
    
    @staticmethod
    def is_safe_query(query):
        """Check if query is safe to execute"""
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE',
            'ALTER', 'CREATE', 'GRANT', 'REVOKE', 'EXECUTE'
        ]
        
        query_upper = query.upper()
        
        # Check for dangerous operations
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return False, f"Operation '{keyword}' is not allowed for security reasons"
        
        # Must start with SELECT
        if not query_upper.strip().startswith('SELECT'):
            return False, "Only SELECT queries are allowed for security reasons"
        
        return True, "Query is safe"

class AppConfig:
    """Application configuration"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/postgres')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        
        # Supabase configuration (update these with your actual values)
        self.supabase_config = {
            'host': os.getenv('SUPABASE_HOST', 'db.your-project-ref.supabase.co'),
            'port': os.getenv('SUPABASE_PORT', '5432'),
            'database': os.getenv('SUPABASE_DB', 'postgres'),
            'user': os.getenv('SUPABASE_USER', 'postgres'),
            'password': os.getenv('SUPABASE_PASSWORD', 'your-password')
        }

class DatabaseManager:
    """Manages database connections"""
    
    def __init__(self, config):
        self.config = config
        self.db = None
    
    def connect(self):
        """Establish database connection using session pooler"""
        try:
            # Use session pooler connection (IPv4 compatible)
            # Format: postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
            host = self.config.supabase_config['host']
            user = self.config.supabase_config['user']
            password = self.config.supabase_config['password']
            database = self.config.supabase_config['database']
            
            # Extract project ref from host for pooler
            if 'supabase.co' in host:
                project_ref = host.replace('db.', '').replace('.supabase.co', '')
                # Use session pooler connection (IPv4 compatible)
                pooler_host = f"aws-0-us-east-1.pooler.supabase.com"
                connection_string = f"postgresql://{user}.{project_ref}:{password}@{pooler_host}:6543/{database}"
            else:
                # Fallback to direct connection
                connection_string = f"postgresql://{user}:{password}@{host}:{self.config.supabase_config['port']}/{database}"
            
            self.db = SQLDatabase.from_uri(
                connection_string,
                include_tables=None,  # Include all tables
                sample_rows_in_table_info=2
            )
            logger.info("Database connection established successfully using pooler")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def get_schema_info(self):
        """Get sanitized schema information"""
        if not self.db:
            return "Database not connected"
        
        try:
            schema_info = self.db.get_table_info()
            return SecureDataHandler.sanitize_schema(schema_info)
        except Exception as e:
            logger.error(f"Error getting schema: {e}")
            return f"Error retrieving schema: {str(e)}"

def get_llm_chain(provider="openai"):
    """Get LLM chain based on provider"""
    if provider == "openai" and st.secrets.get("OPENAI_API_KEY"):
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=st.secrets["OPENAI_API_KEY"]
        )
    elif provider == "groq" and st.secrets.get("GROQ_API_KEY"):
        return ChatGroq(
            model="mixtral-8x7b-32768",
            temperature=0.1,
            api_key=st.secrets["GROQ_API_KEY"]
        )
    else:
        st.error("No valid API key found. Please check your configuration.")
        return None

def get_sql_chain(llm, db):
    """Create SQL generation chain"""
    template = """
    You are a SQL expert. Based on the database schema below, write a complete SQL query to answer the user's question.
    
    <SCHEMA>{schema}</SCHEMA>
    
    Conversation History: {chat_history}
    
    IMPORTANT: Write ONLY the complete SQL query. Do not include any explanations, comments, or markdown formatting.
    
    Examples:
    Question: "which 3 customers have the most orders?"
    SQL Query: SELECT c.name, COUNT(o.id) as order_count FROM customers c LEFT JOIN orders o ON c.id = o.customer_id GROUP BY c.id, c.name ORDER BY order_count DESC LIMIT 3;
    
    Question: "Name 10 customers"
    SQL Query: SELECT name FROM customers LIMIT 10;
    
    Question: "Show me all products"
    SQL Query: SELECT * FROM products;
    
    Now answer this question:
    Question: {question}
    SQL Query:"""
    
    prompt = ChatPromptTemplate.from_template(template)
    
    return prompt | llm | StrOutputParser()

def get_response_chain(llm, db):
    """Create response generation chain"""
    template = """
    You are a helpful SQL assistant. Based on the SQL query results below, provide a clear and concise answer to the user's question.
    
    Question: {question}
    SQL Query: {query}
    Query Results: {result}
    
    Provide a natural language response that answers the user's question based on the data. 
    If the results are empty, explain that no data was found.
    If there are errors, explain what went wrong.
    
    Response:"""
    
    prompt = ChatPromptTemplate.from_template(template)
    
    return prompt | llm | StrOutputParser()

def main():
    """Main application function"""
    
    # Initialize configuration
    config = AppConfig()
    
    # Sidebar configuration
    st.sidebar.title("🔒 Secure AI SQL Chat")
    st.sidebar.markdown("**PostgreSQL + Supabase Version**")
    
    # Provider selection
    provider = st.sidebar.selectbox(
        "Choose AI Provider:",
        ["openai", "groq"],
        help="Select the AI model provider"
    )
    
    # Temperature control
    temperature = st.sidebar.slider(
        "Temperature:",
        min_value=0.0,
        max_value=1.0,
        value=0.1,
        step=0.1,
        help="Controls randomness in AI responses"
    )
    
    # Database connection status
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Database Status")
    
    db_manager = DatabaseManager(config)
    if db_manager.connect():
        st.sidebar.success("✅ Connected to Supabase")
        
        # Show schema info
        with st.sidebar.expander("📋 Database Schema"):
            schema_info = db_manager.get_schema_info()
            st.text(schema_info[:500] + "..." if len(schema_info) > 500 else schema_info)
    else:
        st.sidebar.error("❌ Database connection failed")
        st.error("Cannot connect to database. Please check your Supabase configuration.")
        return
    
    # Main chat interface
    st.title("🔒 Secure AI SQL Chat")
    st.markdown("**Ask questions about your PostgreSQL database using natural language**")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your data..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get LLM
        llm = get_llm_chain(provider)
        if not llm:
            return
        
        # Set temperature
        llm.temperature = temperature
        
        try:
            with st.chat_message("assistant"):
                with st.spinner("🤖 Generating SQL query..."):
                    # Get schema info
                    schema_info = db_manager.get_schema_info()
                    
                    # Create SQL generation chain
                    sql_chain = get_sql_chain(llm, db_manager.db)
                    
                    # Generate SQL query
                    sql_result = sql_chain.invoke({
                        "question": prompt,
                        "chat_history": "",
                        "schema": schema_info
                    })
                    
                    # Clean and validate SQL
                    sql_result = sql_result.strip()
                    if not sql_result or sql_result == "":
                        st.error("Sorry, I couldn't generate a valid SQL query. Please try rephrasing your question.")
                        return
                    
                    if not sql_result.endswith(';'):
                        sql_result = sql_result + ';'
                    
                    # Validate query security
                    is_safe, message = QueryValidator.is_safe_query(sql_result)
                    if not is_safe:
                        st.error(f"Security check failed: {message}")
                        return
                    
                    # Display generated SQL
                    st.info(f"**Generated SQL:**\n```sql\n{sql_result}\n```")
                    
                    # Execute query
                    with st.spinner("🔍 Executing query..."):
                        try:
                            result = db_manager.db.run(sql_result)
                            sanitized_result = SecureDataHandler.sanitize_query_result(result)
                            
                            # Generate natural language response
                            response_chain = get_response_chain(llm, db_manager.db)
                            response = response_chain.invoke({
                                "question": prompt,
                                "query": sql_result,
                                "result": sanitized_result
                            })
                            
                            # Display results
                            st.success("**Query Results:**")
                            st.text(sanitized_result)
                            
                            st.success("**AI Response:**")
                            st.markdown(response)
                            
                            # Add assistant response to chat history
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": f"**SQL Query:**\n```sql\n{sql_result}\n```\n\n**Results:**\n{sanitized_result}\n\n**Response:**\n{response}"
                            })
                            
                        except Exception as e:
                            st.error(f"Query execution error: {str(e)}")
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": f"Error executing query: {str(e)}"
                            })
                            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            logger.error(f"Error in main processing: {e}")
    
    # Sidebar actions
    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **Security Features:**
    - ✅ Data sanitization
    - ✅ Query validation
    - ✅ Sensitive data masking
    - ✅ Cloud deployment ready
    """)

if __name__ == "__main__":
    main() 