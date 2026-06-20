"""
Prometheus Metrics Registry — Phase 10.
"""
from prometheus_client import Counter, Histogram, Gauge

# Latency histogram
agent_execution_seconds = Histogram(
    'agent_execution_seconds',
    'Time spent executing an agent',
    ['agent_name']
)

# Failure counter
agent_failures_total = Counter(
    'agent_failures_total',
    'Total number of agent execution failures',
    ['agent_name']
)

# Retry counter
agent_retry_total = Counter(
    'agent_retry_total',
    'Total number of agent retries',
    ['agent_name']
)

# Token usage counter
agent_tokens_total = Counter(
    'agent_tokens_total',
    'Total number of tokens consumed by the agent',
    ['agent_name']
)

# Phase 11 - RAG Metrics
retrieval_latency_seconds = Histogram(
    'retrieval_latency_seconds',
    'Time spent retrieving RAG context from ChromaDB',
    ['collection']
)

embeddings_generated_total = Counter(
    'embeddings_generated_total',
    'Total number of vectors generated via Gemini Embeddings',
)

vector_search_requests_total = Counter(
    'vector_search_requests_total',
    'Total number of vector search queries sent to ChromaDB',
    ['collection']
)

vector_search_failures_total = Counter(
    'vector_search_failures_total',
    'Total number of vector search failures from ChromaDB',
    ['collection']
)

rag_context_size_tokens = Histogram(
    'rag_context_size_tokens',
    'Size of the generated RAG context in tokens (estimated)',
)

knowledge_agent_duration_seconds = Histogram(
    'knowledge_agent_duration_seconds',
    'Time spent orchestrating the full Knowledge Agent flow',
)

similar_incidents_found_total = Counter(
    'similar_incidents_found_total',
    'Total number of similar historical incidents successfully retrieved',
)

# Phase 18 - Event Bus Metrics
events_published_total = Counter(
    'events_published_total',
    'Total number of events published to the bus',
    ['event_type']
)

events_processed_total = Counter(
    'events_processed_total',
    'Total number of events processed by agents',
    ['event_type', 'agent_name']
)

failed_events_total = Counter(
    'failed_events_total',
    'Total number of events that failed processing',
    ['event_type', 'agent_name']
)

queue_size = Gauge(
    'queue_size',
    'Current number of pending events in the queue'
)

dead_letter_count = Gauge(
    'dead_letter_count',
    'Current number of events in the dead letter queue'
)

event_processing_latency = Histogram(
    'event_processing_latency',
    'Latency of processing an event in seconds',
    ['event_type']
)
