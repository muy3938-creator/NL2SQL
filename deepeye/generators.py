from typing import List, Dict
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from .utils import PROMPT_GENERATE_SKELETON, PROMPT_FILL_SKELETON, PROMPT_ICL_GEN, PROMPT_DNC_GEN

class SQLGenerator:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def generate(self, question: str, schema: str, values: Dict[str, List[str]]) -> str:
        raise NotImplementedError

class SkeletonGenerator(SQLGenerator):
    def generate(self, question: str, schema: str, values: Dict[str, List[str]]) -> str:
        # 1. Generate Skeleton
        skel_prompt = PromptTemplate.from_template(PROMPT_GENERATE_SKELETON)
        skel_chain = skel_prompt | self.llm
        skeleton = skel_chain.invoke({
            "schema": schema,
            "question": question
        }).content
        
        # 2. Fill Skeleton
        fill_prompt = PromptTemplate.from_template(PROMPT_FILL_SKELETON)
        fill_chain = fill_prompt | self.llm
        sql = fill_chain.invoke({
            "skeleton": skeleton,
            "question": question,
            "values": str(values)
        }).content
        
        return self._clean_sql(sql)

    def _clean_sql(self, sql: str) -> str:
        return sql.replace("```sql", "").replace("```", "").strip()

class ICLGenerator(SQLGenerator):
    def generate(self, question: str, schema: str, values: Dict[str, List[str]]) -> str:
        # Hardcoded examples for MVP
        examples = """
        Q: How many students are there?
        SQL: SELECT COUNT(*) FROM students;
        
        Q: List all courses in Computer Science.
        SQL: SELECT course_name FROM courses WHERE department = 'Computer Science';
        """
        
        prompt = PromptTemplate.from_template(PROMPT_ICL_GEN)
        chain = prompt | self.llm
        sql = chain.invoke({
            "schema": schema,
            "examples": examples,
            "question": question,
            "values": str(values)
        }).content
        
        return self._clean_sql(sql)

    def _clean_sql(self, sql: str) -> str:
        return sql.replace("```sql", "").replace("```", "").strip()

class DivideAndConquerGenerator(SQLGenerator):
    def generate(self, question: str, schema: str, values: Dict[str, List[str]]) -> str:
        # Simplified D&C: Just ask LLM to break it down internally
        prompt = PromptTemplate.from_template(PROMPT_DNC_GEN)
        chain = prompt | self.llm
        sql = chain.invoke({
            "schema": schema,
            "question": question,
            "values": str(values)
        }).content
        
        return self._clean_sql(sql)

    def _clean_sql(self, sql: str) -> str:
        return sql.replace("```sql", "").replace("```", "").strip()
