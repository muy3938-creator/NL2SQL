import os
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI

from .schema_linking import SchemaLinker
from .value_retrieval import ValueRetriever
from .generators import SkeletonGenerator, ICLGenerator, DivideAndConquerGenerator
from .checkers import ToolChain
from .selection import ConfidenceSelector
from .utils import get_schema_info

class DeepEyeSQL:
    def __init__(self, db_path: str, openai_api_key: str,openai_base_url: str,model: str):
        self.db_path = db_path
        self.llm = ChatOpenAI(model=model, temperature=0, api_key=openai_api_key,base_url=openai_base_url)
        self.schema = get_schema_info(db_path)
        
        # Initialize components
        self.value_retriever = ValueRetriever(db_path)
        self.schema_linker = SchemaLinker(self.llm)
        self.generators = [
            SkeletonGenerator(self.llm),
            ICLGenerator(self.llm),
            DivideAndConquerGenerator(self.llm)
        ]
        self.checker_chain = ToolChain(self.llm)
        self.selector = ConfidenceSelector(self.llm, db_path)

    def run(self, question: str) -> str:
        print(f"Processing question: {question}")
        
        # Phase 1: Intent Scoping & Semantic Grounding
        print("Phase 1: Intent Scoping...")
        values = self.value_retriever.retrieve(question)
        linked_schema = self.schema_linker.link(question, self.schema, values)
        print(f"Linked Schema (partial): {linked_schema[:100]}...")
        
        # Phase 2: N-version Generation
        print("Phase 2: N-version Generation...")
        candidates = []
        for gen in self.generators:
            try:
                sql = gen.generate(question, linked_schema, values)
                candidates.append(sql)
                print(f"Generated SQL: {sql}")
            except Exception as e:
                print(f"Generation failed: {e}")
            
        # Phase 3: Unit Testing & Revision
        print("Phase 3: Unit Testing & Revision...")
        revised_candidates = []
        for sql in candidates:
            revised_sql = self.checker_chain.run(sql, question, linked_schema)
            revised_candidates.append(revised_sql)
            print(f"Revised SQL: {revised_sql}")
            
        # Phase 4: Selection
        print("Phase 4: Selection...")
        final_sql = self.selector.select(revised_candidates, question)
        print(f"Final Selected SQL: {final_sql}")
        
        return final_sql
