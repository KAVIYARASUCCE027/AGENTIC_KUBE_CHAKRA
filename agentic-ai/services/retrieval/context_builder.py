"""
Context Builder Service — Phase 11.
"""
from typing import List
from schemas.knowledge.chroma_schemas import ChromaIncident, ChromaRunbook, KnowledgeDocument

class ContextBuilder:
    """
    Decouples prompt and context construction logic from the KnowledgeAgent.
    Formats typed retrieved entities into an LLM-digestible string.
    """
    
    def build_rag_context(
        self,
        incidents: List[ChromaIncident],
        runbooks: List[ChromaRunbook],
        docs: List[KnowledgeDocument]
    ) -> str:
        """
        Combines retrieved pieces into a unified RAG context block.
        """
        sections = []
        
        if incidents:
            sections.append("### SIMILAR HISTORICAL INCIDENTS ###")
            for idx, inc in enumerate(incidents, 1):
                sections.append(
                    f"[{idx}] Incident ID: {inc.incident_id}\n"
                    f"Similarity Score: {inc.similarity_score:.2f}\n"
                    f"Root Cause: {inc.root_cause} (Severity: {inc.severity})\n"
                    f"Resolution/Recommendation:\n{inc.recommendation}\n"
                )
                
        if runbooks:
            sections.append("### PROVEN RUNBOOKS ###")
            for idx, rb in enumerate(runbooks, 1):
                sections.append(
                    f"[{idx}] Runbook ID: {rb.runbook_id}\n"
                    f"Target Root Cause: {rb.root_cause_target}\n"
                    f"Similarity Score: {rb.similarity_score:.2f}\n"
                    f"Action Plan:\n{rb.action_plan}\n"
                )
                
        if docs:
            sections.append("### KNOWLEDGE BASE DOCUMENTATION ###")
            for idx, doc in enumerate(docs, 1):
                sections.append(
                    f"[{idx}] Source: {doc.source} (Topic: {doc.topic})\n"
                    f"Similarity Score: {doc.similarity_score:.2f}\n"
                    f"Content:\n{doc.content}\n"
                )
                
        if not sections:
            return "NO RELEVANT HISTORICAL CONTEXT FOUND."
            
        return "\n".join(sections)
