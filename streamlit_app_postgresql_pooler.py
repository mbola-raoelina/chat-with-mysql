# streamlit_app_postgresql_pooler.py - Entry point for PostgreSQL/Supabase pooler version
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'new_version'))
from secure_app_postgresql_pooler import main

if __name__ == "__main__":
    main() 