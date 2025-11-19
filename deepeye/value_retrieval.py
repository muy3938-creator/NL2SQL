from typing import List, Dict, Any
from .utils import get_db_connection

class ValueRetriever:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # In a real scenario without vector DB, we might load values into memory
        # For MVP, we will just do a simple LIKE query on the database for keywords in the question
        pass

    def retrieve(self, question: str, k: int = 5) -> Dict[str, List[str]]:
        """Retrieves relevant values using simple keyword matching."""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        
        # Get all text columns
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        retrieved = {}
        words = question.split()
        potential_keywords = [w for w in words if len(w) > 3] # Simple heuristic
        
        for table in tables:
            table_name = table['name']
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            text_cols = [col['name'] for col in columns if 'TEXT' in col['type'].upper()]
            
            for col in text_cols:
                for keyword in potential_keywords:
                    # Safe parameterized query
                    query = f"SELECT DISTINCT {col} FROM {table_name} WHERE {col} LIKE ?"
                    cursor.execute(query, (f"%{keyword}%",))
                    results = cursor.fetchall()
                    for row in results:
                        val = row[0]
                        key = f"{table_name}.{col}"
                        if key not in retrieved:
                            retrieved[key] = []
                        if val not in retrieved[key]:
                            retrieved[key].append(val)
                            
        conn.close()
        return retrieved
