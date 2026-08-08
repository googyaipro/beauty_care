---
name: cloud-telemetry-monitoring
description: Observability, OpenTelemetry tracing, latency measurement, and health check routes across salon micro-agents.
---

# Cloud Telemetry & Monitoring Skill

## Overview
Provides guidelines for monitoring endpoint health, tracing agent-to-agent (A2A) calls, and logging inter-service requests.

## Implementation Guidelines
1. **Health Check Standard**:
   - Every FastAPI service MUST attach `/healthz`, `/livez`, and `/readyz` endpoints using `attach_health_routes(app, service_name=...)`.

2. **Tracing Steps**:
   - Wrap MCP tool execution and LLM generation blocks in `trace_step(trace_id, step_name, metadata)`.
   - Log latency metrics and error rates to identify performance bottlenecks across container networks.
