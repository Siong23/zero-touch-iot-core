# Zero-Touch IoT Core 

> **A cloud-native platform for automated orchestration, management, and secure operation of IoT applications at the edge.**

## 📌 Description
This project demonstrates an integrated orchestration approach for both **network services** and **cloud-native IoT applications**.  
It combines **network slice management** via [OpenSlice](https://openslice.io/) with **Kubernetes-based IoT service deployment** and **device lifecycle management** through an IoT platform.  
The result is an end-to-end system capable of delivering optimized connectivity and compute for IoT workloads.

---

## ✨ Key Features
- **Hybrid Orchestration** – Manage both network slices (CNFs/VNFs) and IoT microservices from a unified workflow.
- **Cloud-Native Deployment** – Deploy IoT services (MQTT brokers, analytics, APIs) on Kubernetes.
- **Device Lifecycle Management** – Register, monitor, and control IoT devices through an integrated IoT platform.
- **Closed-Loop Automation** – Trigger dynamic network or compute scaling based on device/service telemetry.
- **API-Driven Integration** – IoT platform and network orchestrator communicate via TM Forum-compliant APIs.

---

## Architecture Overview
```
+-----------------------------+
| IoT Devices                 |
| (Sensors, Gateways, etc.)   |
+--------------+--------------+
               |
               v
+-------------------------------------+
| IoT Platform                        |
| - Device mgmt                       |
| - Data ingestion (MQTT, Prometheus) |
| - Rules & automation                |
+--------------+----------------------+
               |
               v
+-----------------------------+      +-----------------------------+
| Kubernetes (IoT workloads)  |<---->| OpenSlice (Network slices)  |
| - Brokers, APIs, analytics  |      | - Slice lifecycle mgmt      |
| - Storage & AI/ML           |      | - TMF APIs                  |
+-----------------------------+      +-----------------------------+
```
---


