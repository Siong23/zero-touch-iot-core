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

4. ZSM Progress Planing Explanation:
```bash
1)First, i will add all the node(iot and edge) into using the frontend UI add node function include the master node also with the node information(username, password, SSH name and password), example i will add 4 node , 2 iot and 2 edge then one of the edge node will become the master, because just edge node can be the master node.

2) Second, after add succesful all the node,  now we can press the "deploy to all node" button,
-first of the steps after press the deploy button is found the master node that we defined, here we can define the one of the edge node will become master at the backend( i want nuc2 become as the master). 
-second, after identify which edge node become the master it will start install all the necessary app (Docker, Helm, K3s Kubernetes, Prometheus, Grafana, Python3 + pip and kuberctl command tool), transer or copy file (offloading_manager.py, q_learning_model.pkl, mediamtx-daemonset.yaml, myapp.yaml, configmap-mediamtx-endpoints.yaml, offloading-manager-pod.yaml, detect.py and /etc/rancher/k3s/k3s.yaml
- Third , Retrieve k3s join token & kubeconfig.

3) Third, after settle the master node now we can do the remaining node. we need to ssh to the node (edge +iot) and install all necessary prerequisites (Python3, Docker and K3s agent if needed, curl, etc). Then most important is join the remaining node(edge+iot) to the master cluster.

4)Fourth, after complete join all node into master cluster, now at the master node need to apply the kubernetes manifests like mediamtx-daemonset.yaml, myapp.yaml, offloading-manager-pod.yaml, configmap-mediamtx-endpoints.yaml, and maybe still have other. Here is make sure all pod is running and camera can streaming from iot node.

5) Fifth, after makes sure the pod is running, now promethoues and grafana will start collecction the data, show the grafana dashboard at the frontend UI dashboard and few data, and correct display all node in the iot nodes page and edge node page. To run the promethoues and grafana it should run comamnd "kubectl port-forward svc/prometheus-operator-kube-p-prometheus -n monitoring 9090:9090" for prometheus and command "kubectl port-forward svc/prometheus-operator-grafana -n monitoring 3000:80" for the grafana in ther master node terminal.
```
