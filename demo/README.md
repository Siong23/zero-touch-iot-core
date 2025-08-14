# Final System Demo Workflow
Stage 0 — Prep
- Package IoT microservices (broker, API, analytics) as containers; push to registry.
- Onboard NSDs/CNFs and service specs in OpenSlice; define slice profiles (URLLC/eMBB).
- Register a few demo devices in the IoT Platform; pre-create topics/rules.
- Set up Observability (Prometheus/Grafana) and a simple Policy Engine (HPA/KEDA + alert rules).

Stage 1 — Instantiate Network & IoT Service
- Operator orders an IoT service with QoS (latency/bw) via OpenSlice portal.
- OpenSlice calls NFVO/VNFM (or CNF orchestrator) → instantiates the Network Slice.
- Kubernetes deploys IoT microservices (via Helm/ArgoCD/kubectl apply).
- IoT Platform publishes service endpoints/credentials; binds registered devices.

Stage 2 — Connect Devices & Ingest Data
- IoT Devices connect to MQTT/HTTP endpoints exposed by the IoT service.
- Telemetry flows → IoT Platform → IoT microservices (ingestion, rules, storage).
- Observability scrapes metrics (service latency, msg rate, CPU, slice KPIs).

Stage 3 — Closed-Loop Optimization
- Policy Engine evaluates SLOs (e.g., P95 latency, backpressure).
- If app pressure ↑ → Kubernetes scales deployments (HPA/KEDA).
- If slice KPIs breach QoS → OpenSlice reconfigures/expands the Network Slice.
- Confirm recovery via dashboards; notify Operator.

Stage 4 — Update & Rollback (Optional)
- Roll out a new analytics version with a rolling update; verify; rollback if needed.

Stage 5 — Tear-Down
- Operator terminates the service: IoT workloads deleted, slice released, devices unbound.
- Export dashboards/logs as demo artifacts.

---

![your-UML-diagram-name](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/Siong23/zero-touch-iot-core/refs/heads/main/demo/workflow.puml)


