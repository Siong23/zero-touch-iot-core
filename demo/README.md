Sequence diagram that represents the demo workflow for the Zero-Touch IoT Core project. It illustrates the interaction from a user initiating a service order to its automated orchestration and deployment across the Kubernetes cluster at the core/edge.

![your-UML-diagram-name](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/Siong23/zero-touch-iot-core/refs/heads/main/demo/workflow.puml)

### Key Points in the Sequence:
- The User initiates the process through a portal (e.g., OSS/BSS or self-service UI).
- TM Forum Open APIs are used for standardized service requests to OpenSlice.
- OpenSlice handles lifecycle management, triggers deployment via Helm/kubectl to the Kubernetes cluster.
- CNFs are deployed in isolated namespaces (representing slices).
- Prometheus and Grafana provide observability back to the UI.
