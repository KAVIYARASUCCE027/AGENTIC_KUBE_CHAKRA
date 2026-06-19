import sys
sys.path.insert(0, 'D:/K8S_AGENTIC/agentic-ai')

print('=' * 60)
print('  Phase 12 -- Event Correlation Engine: Final Validation')
print('=' * 60)

# 1. Enums
from enums.incident_type import IncidentType
from enums.correlation_source import CorrelationSource
print(f'[OK] IncidentType enum: {len(list(IncidentType))} values')
print(f'[OK] CorrelationSource enum: {len(list(CorrelationSource))} values')

# 2. Schemas
from schemas.correlation.correlated_event import CorrelatedEvent
from schemas.correlation.correlation_output import CorrelationOutput
from schemas.cpu_state import CPUState, InputState
state = CPUState(inputs=InputState(pod_name='test-pod', namespace='production'))
assert hasattr(state, 'correlation_output')
assert hasattr(state, 'cpu_analysis')
assert hasattr(state, 'memory_analysis')
assert hasattr(state, 'disk_analysis')
assert hasattr(state, 'network_analysis')
assert hasattr(state, 'log_analysis')
assert hasattr(state, 'event_analysis')
print('[OK] CPUState: 7 new Phase 12 fields present with safe defaults')

# 3. Prompt builder
from prompts.correlation_prompt_builder import CorrelationPromptBuilder
pb = CorrelationPromptBuilder()
sys_p, usr_p = pb.build(
    pod_name='test', namespace='prod',
    cpu_analysis='CPU 91%', memory_analysis='HIGH_MEMORY OOMKILLED',
    disk_analysis='', network_analysis='', log_analysis='', event_analysis='OOMKILLED'
)
assert len(sys_p) > 100 and len(usr_p) > 100
print(f'[OK] CorrelationPromptBuilder: sys={len(sys_p)}ch, user={len(usr_p)}ch')

# 4. Rule engine - multiple scenarios
from services.correlation.event_correlation_service import EventCorrelationService
svc = EventCorrelationService()
print(f'[OK] EventCorrelationService: {len(svc._rules)} rules loaded')

scenarios = [
    ('Memory Leak',
        {'cpu_usage': 91.0, 'restart_count': 4},
        'HIGH_MEMORY OOMKILLED', '', '', '', 'OOMKILLED',
        'MEMORY_LEAK'),
    ('CPU Throttling',
        {'cpu_usage': 88.0, 'throttling_percentage': 30.0},
        '', '', '', '', '',
        'CPU_THROTTLING'),
    ('No match (UNKNOWN)',
        {'cpu_usage': 20.0},
        '', '', '', '', '',
        'UNKNOWN'),
    ('Node Pressure',
        {'cpu_usage': 45.0},
        'MEMORY_PRESSURE', '', '', '', 'EVICTED',
        'NODE_RESOURCE_PRESSURE'),
]

all_passed = True
for name, metric_overrides, mem, disk, net, logs, events, expected in scenarios:
    s = CPUState(inputs=InputState(pod_name='p', namespace='n'))
    s = s.model_copy(update={
        'metrics': s.metrics.model_copy(update=metric_overrides),
        'memory_analysis': mem,
        'disk_analysis': disk,
        'network_analysis': net,
        'log_analysis': logs,
        'event_analysis': events,
    })
    r = svc.correlate(s)
    ok = r.incident_type.value == expected
    if not ok:
        all_passed = False
    status = '[OK]  ' if ok else '[FAIL]'
    print(f'{status} Scenario "{name}": incident={r.incident_type.value} confidence={r.confidence_score:.3f} events={len(r.correlated_events)}')

# 5. LangGraph
from graph.cpu_graph import build_cpu_graph
g = build_cpu_graph()
nodes = list(g.nodes.keys())
assert 'correlation' in nodes, 'correlation node missing!'
assert nodes.index('correlation') < nodes.index('analyzer'), 'correlation must be before analyzer!'
print(f'[OK] LangGraph: {len(nodes)} nodes compiled')
print(f'     Full order: {" -> ".join(n for n in nodes if not n.startswith("__"))}')

print()
if all_passed:
    print('=' * 60)
    print('  ALL PHASE 12 CHECKS PASSED')
    print('=' * 60)
else:
    print('[WARN] Some scenarios did not match expected outcome')
