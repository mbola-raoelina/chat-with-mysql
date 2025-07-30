#!/usr/bin/env python3
"""
Simple Database Connection Tester
Use this to manually test your MySQL connection and run queries
"""

import mysql.connector
from mysql.connector import Error
import sys

def test_connection(host, user, password, database, port=3306):
    """Test database connection"""
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"✅ Connected to MySQL Server version {db_info}")
            
            cursor = connection.cursor()
            cursor.execute("select database();")
            record = cursor.fetchone()
            print(f"✅ Connected to database: {record[0]}")
            
            return connection, cursor
        else:
            print("❌ Failed to connect to database")
            return None, None
            
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return None, None

def show_tables(cursor):
    """Show all tables in the database"""
    try:
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print("\n📋 Available Tables:")
        for table in tables:
            print(f"  - {table[0]}")
        return tables
    except Error as e:
        print(f"❌ Error showing tables: {e}")
        return []

def describe_table(cursor, table_name):
    """Show table structure"""
    try:
        cursor.execute(f"DESCRIBE {table_name};")
        columns = cursor.fetchall()
        print(f"\n📊 Table Structure for '{table_name}':")
        print("Column Name\t\tType\t\tNull\tKey\tDefault\tExtra")
        print("-" * 80)
        for column in columns:
            print(f"{column[0]}\t\t{column[1]}\t\t{column[2]}\t{column[3]}\t{column[4]}\t{column[5]}")
        return columns
    except Error as e:
        print(f"❌ Error describing table: {e}")
        return []

def run_query(cursor, query):
    """Run a custom query"""
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Get column names
        column_names = [desc[0] for desc in cursor.description]
        
        print(f"\n🔍 Query Results:")
        print("Query:", query)
        print("-" * 80)
        
        # Print column headers
        for col in column_names:
            print(f"{col:<20}", end="")
        print()
        print("-" * 80)
        
        # Print results
        for row in results:
            for value in row:
                print(f"{str(value):<20}", end="")
            print()
            
        print(f"\n📊 Total rows: {len(results)}")
        return results
        
    except Error as e:
        print(f"❌ Error running query: {e}")
        return []

def main():
    print("🔍 MySQL Database Connection Tester")
    print("=" * 50)
    
    # Get connection details
    host = input("Enter host (default: localhost): ").strip() or "localhost"
    port = input("Enter port (default: 3306): ").strip() or "3306"
    user = input("Enter username (default: root): ").strip() or "root"
    password = input("Enter password: ").strip()
    database = input("Enter database name: ").strip()
    
    print(f"\n🔗 Connecting to {host}:{port}/{database} as {user}...")
    
    # Test connection
    connection, cursor = test_connection(host, user, password, database, int(port))
    
    if connection is None:
        print("❌ Cannot proceed without database connection")
        return
    
    # Show tables
    tables = show_tables(cursor)
    
    if tables:
        # Interactive query mode
        print("\n🎯 Interactive Query Mode")
        print("Type 'quit' to exit, 'tables' to show tables, 'describe <table>' to see table structure")
        
        while True:
            try:
                query = input("\n🔍 Enter SQL query: ").strip()
                
                if query.lower() == 'quit':
                    break
                elif query.lower() == 'tables':
                    show_tables(cursor)
                elif query.lower().startswith('describe '):
                    table_name = query[9:].strip()
                    describe_table(cursor, table_name)
                elif query:
                    run_query(cursor, query)
                else:
                    print("Please enter a query or 'quit' to exit")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    # Close connection
    if connection and connection.is_connected():
        cursor.close()
        connection.close()
        print("\n✅ Database connection closed")

if __name__ == "__main__":
    main() 