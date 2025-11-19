from typing import List, Tuple
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from .utils import PROMPT_REVISE_SQL
import sqlglot
import re

class Checker:
    def check(self, sql: str) -> Tuple[bool, str]:
        """Returns (is_valid, error_message)"""
        raise NotImplementedError

class SyntaxChecker(Checker):
    def check(self, sql: str) -> Tuple[bool, str]:
        try:
            sqlglot.transpile(sql, read="sqlite", write="sqlite")
            return True, ""
        except Exception as e:
            return False, f"Syntax Error: {str(e)}"

class JoinChecker(Checker):
    def check(self, sql: str) -> Tuple[bool, str]:
        # Basic check: if JOIN is used, ON must be used
        if "JOIN" in sql.upper() and "ON" not in sql.upper():
            return False, "JOIN clause missing ON condition."
        return True, ""

class ToolChain:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.checkers = [
            SyntaxChecker(),
            JoinChecker()
        ]

    def run(self, sql: str, question: str, schema: str) -> str:
        current_sql = sql
        
        for checker in self.checkers:
            is_valid, error = checker.check(current_sql)
            if not is_valid:
                print(f"Checker found error: {error}. Revising...")
                current_sql = self._revise(current_sql, question, error)
        
        return current_sql

    def _revise(self, sql: str, question: str, error: str) -> str:
        prompt = PromptTemplate.from_template(PROMPT_REVISE_SQL)
        chain = prompt | self.llm
        revised = chain.invoke({
            "question": question,
            "sql": sql,
            "error": error
        }).content
        return revised.replace("```sql", "").replace("```", "").strip()
