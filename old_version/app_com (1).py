from dotenv import load_dotenv # Charge les variables d'environnement à partir du fichier .env.
from langchain_core.messages import AIMessage, HumanMessage # Importe les classes pour représenter les messages de l'IA et de l'utilisateur.
from langchain_core.prompts import ChatPromptTemplate # Importe la classe pour créer des modèles de prompts pour les conversations.
from langchain_core.runnables import RunnablePassthrough # Importe une classe pour passer les données à travers les étapes du pipeline.
from langchain_community.utilities import SQLDatabase # Importe la classe pour interagir avec une base de données SQL.
from langchain_core.output_parsers import StrOutputParser # Importe un parseur pour convertir la sortie du modèle en chaîne de caractères.
from langchain_openai import ChatOpenAI # Importe la classe pour utiliser le modèle de chat OpenAI.
from langchain_groq import ChatGroq # Importe la classe pour utiliser le modèle de chat Groq.
import streamlit as st # Importe la bibliothèque Streamlit pour créer une interface web interactive.

def init_database(user: str, password: str, host: str, port: str, database: str) -> SQLDatabase:
    # Initialise une connexion à la base de données SQL en utilisant les informations fournies.
    db_uri = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}" # Construit l'URI de connexion à la base de données.
    return SQLDatabase.from_uri(db_uri) # Crée et retourne une instance de SQLDatabase.

def get_sql_chain(db):
    # Crée une chaîne pour générer des requêtes SQL à partir des questions de l'utilisateur.
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
        """ # Définit le modèle de prompt pour générer la requête SQL.
        
    prompt = ChatPromptTemplate.from_template(template) # Crée un modèle de prompt à partir du template.
    
    #llm = ChatOpenAI(model="gpt-4-0125-preview") # Initialise le modèle de chat OpenAI.
    llm = ChatGroq(model="mixtral-8x7b-32768", temperature=0) # Initialise le modèle de chat Groq.
    
    def get_schema(_):
        # Récupère les informations du schéma de la base de données.
        return db.get_table_info() # Retourne les informations du schéma de la table.
    
    return (
        RunnablePassthrough.assign(schema=get_schema) # Assigne le schéma de la base de données aux variables.
        | prompt # Passe les variables au modèle de prompt.
        | llm # Passe le prompt au modèle de langage.
        | StrOutputParser() # Parse la sortie du modèle en chaîne de caractères.
    )
        
def get_response(user_query: str, db: SQLDatabase, chat_history: list):
    # Crée une chaîne pour générer une réponse en langage naturel à partir de la requête SQL et de sa réponse.
    sql_chain = get_sql_chain(db) # Obtient la chaîne pour générer la requête SQL.
    
    template = """
        You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
        Based on the table schema below, question, sql query, and sql response, write a natural language response.
        <SCHEMA>{schema}</SCHEMA>

        Conversation History: {chat_history}
        SQL Query: <SQL>{query}</SQL>
        User question: {question}
        SQL Response: {response}""" # Définit le modèle de prompt pour générer la réponse en langage naturel.
    
    prompt = ChatPromptTemplate.from_template(template) # Crée un modèle de prompt à partir du template.
    
    # llm = ChatOpenAI(model="gpt-4-0125-preview") # Initialise le modèle de chat OpenAI.
    llm = ChatGroq(model="mixtral-8x7b-32768", temperature=0) # Initialise le modèle de chat Groq.
    
    chain = (
        RunnablePassthrough.assign(query=sql_chain).assign( # Assigne la requête SQL générée aux variables.
            schema=lambda _: db.get_table_info(), # Récupère le schéma de la base de données.
            response=lambda vars: db.run(vars["query"]), # Exécute la requête SQL et récupère la réponse.
        )
        | prompt # Passe les variables au modèle de prompt.
        | llm # Passe le prompt au modèle de langage.
        | StrOutputParser() # Parse la sortie du modèle en chaîne de caractères.
    )
    
    return chain.invoke({ # Exécute la chaîne avec les entrées.
        "question": user_query, # La question de l'utilisateur.
        "chat_history": chat_history, # L'historique des conversations.
    })
        
    
if "chat_history" not in st.session_state:
    # Initialise l'historique des conversations si ce n'est pas déjà fait.
    st.session_state.chat_history = [
        AIMessage(content="Hello! I'm a SQL assistant. Ask me anything about your database."), # Ajoute un message de bienvenue de l'IA.
    ]

load_dotenv() # Charge les variables d'environnement à partir du fichier .env.

st.set_page_config(page_title="Chat with MySQL", page_icon=":speech_balloon:") # Configure la page Streamlit.

st.title("Chat with MySQL") # Définit le titre de l'application.

with st.sidebar:
    # Crée une barre latérale pour les paramètres de connexion à la base de données.
    st.subheader("Settings") # Définit le sous-titre de la barre latérale.
    st.write("This is a simple chat application using MySQL. Connect to the database and start chatting.") # Affiche une description de l'application.
    
    st.text_input("Host", value="localhost", key="Host") # Crée un champ de texte pour l'hôte de la base de données.
    st.text_input("Port", value="3306", key="Port") # Crée un champ de texte pour le port de la base de données.
    st.text_input("User", value="root", key="User") # Crée un champ de texte pour le nom d'utilisateur de la base de données.
    st.text_input("Password", type="password", value="admin", key="Password") # Crée un champ de texte pour le mot de passe de la base de données.
    st.text_input("Database", value="Chinook", key="Database") # Crée un champ de texte pour le nom de la base de données.
    
    if st.button("Connect"):
        # Crée un bouton pour se connecter à la base de données.
        with st.spinner("Connecting to database..."): # Affiche un spinner pendant la connexion.
            db = init_database(
                st.session_state["User"],
                st.session_state["Password"],
                st.session_state["Host"],
                st.session_state["Port"],
                st.session_state["Database"]
            ) # Initialise la connexion à la base de données.
            st.session_state.db = db # Stocke l'instance de SQLDatabase dans la session.
            st.success("Connected to database!") # Affiche un message de succès après la connexion.
    
for message in st.session_state.chat_history:
    # Affiche l'historique des conversations.
    if isinstance(message, AIMessage):
        # Affiche les messages de l'IA.
        with st.chat_message("AI"):
            st.markdown(message.content) # Affiche le contenu du message de l'IA.
    elif isinstance(message, HumanMessage):
        # Affiche les messages de l'utilisateur.
        with st.chat_message("Human"):
            st.markdown(message.content) # Affiche le contenu du message de l'utilisateur.

user_query = st.chat_input("Type a message...") # Crée un champ de saisie pour l'utilisateur.
if user_query is not None and user_query.strip() != "":
    # Si l'utilisateur a saisi une requête.
    st.session_state.chat_history.append(HumanMessage(content=user_query)) # Ajoute la requête de l'utilisateur à l'historique des conversations.
    
    with st.chat_message("Human"):
        # Affiche la requête de l'utilisateur dans la fenêtre de chat.
        st.markdown(user_query) # Affiche le contenu de la requête de l'utilisateur.
        
    with st.chat_message("AI"):
        # Affiche la réponse de l'IA dans la fenêtre de chat.
        response = get_response(user_query, st.session_state.db, st.session_state.chat_history) # Obtient la réponse de l'IA à partir de la requête de l'utilisateur.
        st.markdown(response) # Affiche la réponse de l'IA.
        #sql_chain = get_sql_chain(st.session_state.db)
        #response = sql_chain.invoke({
          #"chat_history": st.session_state.chat_history,
          #"question": user_query,           
        #})
        #st.markdown(response)
        
           
        
    st.session_state.chat_history.append(AIMessage(content=response)) # Ajoute la réponse de l'IA à l'historique des conversations.