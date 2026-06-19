"""
Knowledge Agent — Phase 11.
"""
import time
import logging
from typing import List

from agents.base_agent import BaseAgent
from schemas.cpu_state import CPUState
from schemas.knowledge.knowledge_output import KnowledgeAgentOutput
from services.retrieval.retriever_service import RetrieverService
from services.retrieval.context_builder import ContextBuilder
from utils.metrics import knowledge_agent_duration_seconds, rag_context_size_tokens

logger = logging.getLogger(__name__)

class KnowledgeAgent(BaseAgent):
    def __init__(self):
        self._retriever = RetrieverService()
        self._context_builder = ContextBuilder()

    @property
    def name(self) -> str:
        return "knowledge"

    def execute(self, state: CPUState) -> CPUState:
        start_t = time.perf_counter()
        try:
            # 1. We construct a search signature representing the current state
            # Usually we search using the metrics summary and the identified root cause.
            root_cause_str = "UNKNOWN"
            severity_str = state.analyzer_output.severity.value if state.analyzer_output and state.analyzer_output.severity else None
            
            if state.root_cause_output and state.root_cause_output.root_cause:
                root_cause_str = state.root_cause_output.root_cause.value
                
            incident_signature = (
                f"Root Cause: {root_cause_str}. "
                f"CPU Usage: {state.metrics.cpu_usage}%. "
                f"Restarts: {state.metrics.restart_count}. "
                f"Abnormalities: {', '.join(a.value for a in state.analyzer_output.abnormalities)}"
            )

            # 2. Retrieve strongly-typed semantic matches
            incidents = self._retriever.retrieve_similar_incidents(
                incident_signature=incident_signature,
                severity=severity_str,
                root_cause=root_cause_str if root_cause_str != "UNKNOWN" else None
            )
            runbooks = self._retriever.retrieve_runbooks(root_cause=root_cause_str)
            
            # Use root cause and abnormalities as doc search query
            doc_query = f"{root_cause_str} kubernetes troubleshooting"
            docs = self._retriever.retrieve_documents(search_query=doc_query)

            # 3. Build context string
            rag_context = self._context_builder.build_rag_context(incidents, runbooks, docs)

            # 4. Construct metadata & Output
            source_count = len(incidents) + len(runbooks) + len(docs)
            confidence = 0.0
            
            if source_count > 0:
                # Naive average of similarity scores, maxed out logic can be improved later
                total_sim = sum(i.similarity_score for i in incidents) + \
                            sum(r.similarity_score for r in runbooks) + \
                            sum(d.similarity_score for d in docs)
                confidence = total_sim / source_count

            output = KnowledgeAgentOutput(
                rag_context=rag_context,
                confidence=confidence,
                source_count=source_count,
                retrieved_incident_ids=[i.incident_id for i in incidents],
                retrieved_runbook_ids=[r.runbook_id for r in runbooks],
                retrieved_document_ids=[d.doc_id for d in docs]
            )
            
            # Record RAG context size metric (approximate token count -> 4 chars = 1 token roughly)
            rag_context_size_tokens.observe(len(rag_context) / 4)

            logger.info(f"KnowledgeAgent retrieved {source_count} sources with confidence {confidence:.2f}")

        except Exception as e:
            logger.error(f"KnowledgeAgent failed during execution: {e}")
            output = KnowledgeAgentOutput() # Empty fallback
            
        finally:
            knowledge_agent_duration_seconds.observe(time.perf_counter() - start_t)

        return state.model_copy(update={"knowledge_output": output})
