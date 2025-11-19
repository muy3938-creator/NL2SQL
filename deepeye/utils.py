import os
import sqlite3
from typing import List, Dict, Any, Optional

# --- Database Utils ---

def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Establishes a connection to the SQLite database."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_schema_info(db_path: str) -> str:
    """Retrieves the schema information (CREATE TABLE statements) from the database."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    schema_str = ""
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table['name']
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        create_stmt = f"CREATE TABLE {table_name} (\n"
        cols_defs = []
        for col in columns:
            cols_defs.append(f"  {col['name']} {col['type']}")
        create_stmt += ",\n".join(cols_defs)
        create_stmt += "\n);\n"
        
        schema_str += create_stmt + "\n"
        
    conn.close()
    return schema_str

def execute_sql(db_path: str, sql: str) -> List[Any]:
    """Executes a SQL query and returns the results."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        # Convert Row objects to tuples or dicts if needed, for now returning list of tuples
        return [tuple(row) for row in results]
    except sqlite3.Error as e:
        return [f"Error: {e}"]
    finally:
        conn.close()

# --- Prompts ---

PROMPT_DIRECT_LINKING = """
You are a database expert. Given the user question and the database schema, identify the relevant tables and columns.
Schema:
{schema}

Question: {question}

Relevant Values: {values}

List the relevant tables and columns in the format: Table.Column
"""

PROMPT_GENERATE_SKELETON = """
You are a SQL expert. Given the question and schema, generate a SQL skeleton (without specific values/conditions first, just the structure).
Schema:
{schema}

Question: {question}

Return ONLY the SQL skeleton.
"""

PROMPT_FILL_SKELETON = """
You are a SQL expert. Fill in the details for this SQL skeleton based on the question.
Skeleton:
{skeleton}

Question: {question}

Values: {values}

Return ONLY the valid SQL query.
"""

PROMPT_ICL_GEN = """
You are a SQL expert. Generate a SQL query for the question based on the schema and similar examples.
Schema:
{schema}

Examples:
{examples}

Question: {question}

Values: {values}

Return ONLY the SQL query.
"""

PROMPT_DNC_GEN = """
You are a SQL expert. Solve this complex question by breaking it down if necessary.
Schema:
{schema}

Question: {question}

Values: {values}

Return ONLY the final SQL query.
"""

PROMPT_REVISE_SQL = """
You are a SQL debugging expert. The following SQL query has an error.
Question: {question}
SQL: {sql}
Error/Directive: {error}

Fix the SQL query. Return ONLY the fixed SQL.
"""

PROMPT_PAIRWISE_VOTE = """
Compare two SQL queries for the given question.
Question: {question}

SQL A: {sql_a}
SQL B: {sql_b}

Which one is better/correct? Return 'A' or 'B'.
"""
