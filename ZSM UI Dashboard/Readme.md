1. Applications to Install in Edge Node:
```bash
1. Docker - Container runtime
2. K3s - Kubernetes master/worker
3. Helm - Package manager
4. Python3 + pip - For scripts
5. kubectl - K8s command tool
```

2. File require in Master Node:
```bash
1. offloading_manager.py - RL controller script
2. q_learning_model.pkl - Trained AI model
3. mediamtx-daemonset.yaml - Streaming service
4. myapp.yaml - Object detection app
5. configmap-mediamtx-endpoints.yaml - Camera URLs
6. offloading-manager-pod.yaml - RL app deployment
7. detect.py - Object detection code
8. /etc/rancher/k3s/k3s.yaml - K8s config (auto-generated)
```

3. Applications to Install in Iot Node:
```bash
1. Docker - Container runtime  
2. K3s agent - Join to cluster
3. Python3 - Basic Python
```
