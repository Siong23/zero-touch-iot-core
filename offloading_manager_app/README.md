1. Build the docker image:
```bash
docker build -t <image-name>:<tag> .
```

2. Push to repository (ensure you are logged in to your container registry before pushing):
```bash
docker tag <image-name>:<tag> <registry>/<image-name>:<tag>
docker push <registry>/<image-name>:<tag>
```

3. (optional) Run using Docker to test your image locally before deploying:
```bash
docker run --rm --network host -v /etc/rancher/k3s/k3s.yaml:/etc/rancher/k3s/k3s.yaml:ro <image-name>:<tag>
```

4. Deploy using Kubernetes:

    Create a single pod manifest:
   
```yaml
# offloading-manager-pod.yaml

apiVersion: v1
kind: Pod
metadata:
  name: offloading-manager
spec:
  nodeSelector:
    kubernetes.io/hostname: nuc2
  hostNetwork: true
  containers:
    - name: offloading-manager
      image: <image-name>:<tag>
      volumeMounts:
        - name: k3s-config
          mountPath: /root/.kube/k3s.yaml   # Inside container
          readOnly: true
      ##securityContext:
        ##runAsUser: 0
  volumes:
    - name: k3s-config
      hostPath:
        path: /etc/rancher/k3s/k3s.yaml
        type: File
  ```

  Apply the pod:
```bash
kubectl apply -f offloading-manager-pod.yaml
```
