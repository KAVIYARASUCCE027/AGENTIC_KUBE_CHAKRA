"""
Memory Service — Phase 9.

Orchestrates database operations, similarity matching, and context generation.
"""
import time
import logging
from typing import List, Dict, Any

from schemas.cpu_state import CPUState
from schemas.memory.incident_record import (
    IncidentRecord, MetricsSnapshot, AnalyzerSnapshot, 
    RootCauseSnapshot, RecommendationSnapshot, ActionPlanSnapshot
)
from schemas.memory_output import MemoryOutputState, SimilarIncident, HistoricalPattern, MemorySummary
from enums.memory_source import MemorySource
from repositories.incident_repository import IncidentRepository
from repositories.memory_repository import MemoryRepository
from utils.memory_logger import MemoryLogger
from services.embeddings.embedding_service import EmbeddingService
from services.vector_store.chroma_service import ChromaService

logger = logging.getLogger(__name__)
mem_logger = MemoryLogger("services.memory_service")


class MemoryService:
    def __init__(self):
        self._incident_repo = IncidentRepository()
        self._memory_repo = MemoryRepository()
        self._embedding = EmbeddingService()
        self._chroma = ChromaService()

    def save_incident(self, state: CPUState) -> str:
        """Map CPUState to IncidentRecord and persist it."""
        start = time.monotonic()
        try:
            m = state.metrics
            ao = state.analyzer_output
            rc = state.root_cause_output
            ro = state.recommendation_output
            ap = state.action_plan_output

            record = IncidentRecord(
                execution_id=state.metadata.execution_id,
                pod_name=state.inputs.pod_name,
                namespace=state.inputs.namespace,
                metrics=MetricsSnapshot(
                    cpu_usage=m.cpu_usage,
                    avg_cpu_5m=m.avg_cpu_last_5m,
                    avg_cpu_15m=m.avg_cpu_last_15m,
                    cpu_trend=m.cpu_trend.value,
                    cpu_limit=m.cpu_limit,
                    cpu_request=m.cpu_request,
                    restart_count=m.restart_count,
                    replica_count=m.replica_count,
                ),
                analyzer=AnalyzerSnapshot(
                    health_status=ao.health_status,
                    severity=ao.severity,
                    abnormality=ao.abnormality,
                    confidence=ao.confidence,
                ),
                root_cause=RootCauseSnapshot(
                    root_cause=rc.root_cause,
                    confidence=rc.confidence,
                    evidence=list(rc.evidence),
                ),
                recommendation=RecommendationSnapshot(
                    recommendations=list(ro.recommendations),
                    confidence=ro.confidence,
                ),
                action_plan=ActionPlanSnapshot(
                    action_types=[a.action_type for a in ap.actions],
                    priority=ap.priority.value,
                    risk=ap.risk.value,
                    confidence=ap.confidence,
                )
            )

            incident_id = self._incident_repo.save(record)
            
            # --- Phase 11: Continuous Sync to ChromaDB ---
            try:
                # 1. Create a semantic signature of the incident
                signature = (
                    f"Root Cause: {rc.root_cause.value}. "
                    f"Severity: {ao.severity.value}. "
                    f"CPU Usage: {m.cpu_usage}%. "
                    f"Restarts: {m.restart_count}. "
                    f"Abnormalities: {ao.abnormality.value}."
                )
                
                # 2. Extract Recommendation text
                recommendation_text = ", ".join(ro.recommendations)
                
                # 3. Generate Vector
                vector = self._embedding.generate_embedding(signature)
                
                if vector:
                    # 4. Upsert to Chroma
                    self._chroma.add_incident(
                        incident_id=incident_id,
                        document=recommendation_text,
                        metadata={
                            "incident_id": incident_id,
                            "severity": ao.severity.value,
                            "root_cause": rc.root_cause.value
                        },
                        vector=vector
                    )
            except Exception as chroma_e:
                logger.warning(f"Failed to sync incident {incident_id} to ChromaDB: {chroma_e}")
            # ----------------------------------------------
            
            elapsed_ms = int((time.monotonic() - start) * 1000)
            mem_logger.log_save_latency(record.incident_id, elapsed_ms)
            return record.incident_id

        except Exception as e:
            mem_logger.log_error("save_incident", str(e))
            raise

    def retrieve_context(self, pod_name: str, namespace: str, root_cause: str, severity: str) -> MemoryOutputState:
        """Find similar incidents and build context summary."""
        start = time.monotonic()
        try:
            raw_similar = self._memory_repo.find_similar(pod_name, namespace, root_cause, severity)
            raw_patterns = self._memory_repo.extract_patterns(pod_name, namespace)

            similar_incidents = []
            for doc in raw_similar:
                score = doc.get("similarity_score", 0.0)
                sim = SimilarIncident(
                    incident_id=doc["incident_id"],
                    pod_name=doc["pod_name"],
                    timestamp=str(doc["timestamp"]),
                    root_cause=doc["root_cause"]["root_cause"],
                    severity=doc["analyzer"]["severity"],
                    similarity_score=score,
                    resolution_status=doc["status"],
                )
                similar_incidents.append(sim)
                mem_logger.log_similarity_score(sim.incident_id, score)

            historical_patterns = []
            for pat in raw_patterns:
                historical_patterns.append(HistoricalPattern(
                    pattern_type="REPEATED_ROOT_CAUSE",
                    frequency=pat["count"],
                    description=f"Root cause '{pat['_id']}' has occurred {pat['count']} times in the last 30 days."
                ))

            summary = self._build_memory_context(similar_incidents, historical_patterns)

            elapsed_ms = int((time.monotonic() - start) * 1000)
            mem_logger.log_retrieval(len(similar_incidents), len(historical_patterns), elapsed_ms)

            return MemoryOutputState(
                similar_incidents=similar_incidents,
                historical_patterns=historical_patterns,
                memory_summary=summary,
                incident_count=len(similar_incidents),
                source=MemorySource.MONGODB
            )
        except Exception as e:
            mem_logger.log_error("retrieve_context", str(e))
            raise

    def _build_memory_context(self, similar: List[SimilarIncident], patterns: List[HistoricalPattern]) -> MemorySummary:
        """Generate a human-readable text block for AI consumption."""
        if not similar and not patterns:
            return MemorySummary(context="No history available.", key_takeaways=[])

        context = f"{len(similar)} similar incidents found recently. "
        takeaways = []

        if patterns:
            takeaways.extend([p.description for p in patterns])
            
        resolutions = [s.resolution_status for s in similar]
        resolved_count = resolutions.count("RESOLVED")
        
        if similar:
            context += f"{resolved_count} out of {len(similar)} were resolved successfully."

        return MemorySummary(context=context, key_takeaways=takeaways)
