# Zero-Touch IoT Core 

> **A cloud-native platform for automated orchestration, management, and secure operation of IoT applications at the edge.**

`zero-touch-iot-core` is designed to simplify and automate the deployment, lifecycle management, and monitoring of IoT services in 5G-enabled networks. It uses open standards (TM Forum APIs), service orchestration (OpenSlice), and cloud-native technologies (Kubernetes, CNFs) to enable secure, scalable, and fully zero-touch operations—ideal for telco and smart infrastructure deployments.

---

## Key Features

- **Zero-Touch Service Lifecycle** — Fully automated provisioning, scaling, and decommissioning.
- **Edge-Oriented Orchestration** — Seamless core/edge CNF deployments using Kubernetes and Helm.
- **Slice Isolation** — Namespace-based isolation for secure multi-tenancy.
- **IoT-Optimized CNFs** — MQTT broker, AI inference, InfluxDB, and more.
- **Monitoring Ready** — Prometheus & Grafana pre-integrated for observability.
- **TM Forum Compliant** — RESTful APIs for service/slice orders via OpenSlice.

---

## Architecture Overview
                      +------------------------------------------+
                      |        OSS / BSS / Self-Service UI       |
                      |  (Customer Mgmt, Slice Ordering, Portal) |
                      +---------------------↑--------------------+
                                            | TM Forum Open APIs
                                            ↓
           +------------------------------------------------------------+
           |              OpenSlice (Service Orchestrator)              |
           | - Manages service/slice lifecycles                         |
           | - Handles catalogs and orders                              |
           | - Translates service requests into Helm/K8s deployments    |
           +--------------------------------↓---------------------------+
                                    Kubernetes API (kubectl / Helm)
                                            ↓
           +------------------------------------------------------------+
           |           Kubernetes Cluster (Core / Edge Nodes)           |
           | - Runs CNFs (e.g., MQTT, InfluxDB, AI Inference)           |
           | - Namespace-based isolation for each tenant/slice          |
           | - Autoscaling, Monitoring, Service Mesh (Istio/Linkerd)    |
           +--------------------------------↓---------------------------+
                                  CNF Pods and Services


---

## 📦 Installation

### Prerequisites

- Kubernetes v1.24+
- Helm v3.11+
- OpenSlice + TMF APIs
- (Optional) OpenStack if hybrid deployment needed

### 1. Clone the Repo

```bash
git clone https://github.com/your-org/zero-touch-iot-core.git
cd zero-touch-iot-core
```

### 2. Install via Helm
```
helm install ztiot ./helm/ztiot-core/ --namespace iot-platform --create-namespace
```
### 3. Access the Portal
```
http://<your-node-ip>:3000
```

## Project Structure
```
zero-touch-iot-core/
├── helm/                   # Helm charts for CNF & platform deployment
├── orchestrator/           # OpenSlice TMF service definitions and templates
├── cnfs/                   # CNF descriptors (e.g., MQTT broker, AI inference)
├── monitoring/             # Grafana dashboards, Prometheus configs
├── scripts/                # Helper scripts for automation
├── docs/                   # Architecture diagrams and usage docs
└── README.md
```

## Example CNF Deployment
```
helm install mqtt-core ./cnfs/mqtt-broker/ --namespace slice-smartfactory
```

## Documentation
Refer to the docs/ folder for:
- System Overview
- Installation Guides
- CNF Packaging and Deployment
- TM Forum API Integration
- Monitoring Setup
- Slice Template Design
