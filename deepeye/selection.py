from typing import List, Dict, Tuple
from collections import Counter
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from .utils import execute_sql, PROMPT_PAIRWISE_VOTE

class ConfidenceSelector:
    def __init__(self, llm: ChatOpenAI, db_path: str):
        self.llm = llm
        self.db_path = db_path

    def select(self, candidates: List[str], question: str) -> str:
        if not candidates:
            return ""
        
        # 1. Execute and Cluster
        clusters = self._cluster_candidates(candidates)
        
        # 2. Calculate Confidence
        # Sort clusters by size (descending)
        sorted_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)
        
        top_cluster_key = sorted_clusters[0][0]
        top_cluster_sqls = sorted_clusters[0][1]
        
        confidence = len(top_cluster_sqls) / len(candidates)
        print(f"Top cluster confidence: {confidence:.2f}")
        
        # 3. Selection Logic
        THRESHOLD = 0.6
        if confidence > THRESHOLD:
            print("High confidence shortcut taken.")
            return top_cluster_sqls[0]
        else:
            print("Low confidence. Triggering pairwise voting...")
            return self._pairwise_voting(sorted_clusters, question)

    def _cluster_candidates(self, candidates: List[str]) -> Dict[str, List[str]]:
        clusters = {}
        for sql in candidates:
            # Execute SQL to get result signature
            result = execute_sql(self.db_path, sql)
            # Use string representation of result as key
            key = str(result)
            if key not in clusters:
                clusters[key] = []
            clusters[key].append(sql)
        return clusters

    def _pairwise_voting(self, sorted_clusters: List[Tuple[str, List[str]]], question: str) -> str:
        # Take top 2 clusters for simplicity in MVP
        if len(sorted_clusters) < 2:
            return sorted_clusters[0][1][0]
            
        c1_sqls = sorted_clusters[0][1]
        c2_sqls = sorted_clusters[1][1]
        
        sql_a = c1_sqls[0]
        sql_b = c2_sqls[0]
        
        prompt = PromptTemplate.from_template(PROMPT_PAIRWISE_VOTE)
        chain = prompt | self.llm
        vote = chain.invoke({
            "question": question,
            "sql_a": sql_a,
            "sql_b": sql_b
        }).content.strip().upper()
        
        if 'A' in vote:
            return sql_a
        else:
            return sql_b
