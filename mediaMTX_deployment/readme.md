Create mediamtx-daemonset.yaml:
```bash
nano mediamtx-daemonset.yaml
```


Delete mediamtx-daemonset.yaml:
```bash
kubectl delete -f mediamtx-daemonset.yaml
```


Deploy the mediamtx-daemonset.yaml:
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: mediamtx
spec:
  selector:
    matchLabels:
      app: mediamtx
  template:
    metadata:
      labels:
        app: mediamtx
    spec:
      nodeSelector:
        role: iot
      hostNetwork: true          # <-- Each pod binds directly to the node’s network namespace
      dnsPolicy: ClusterFirstWithHostNet
      containers:
      - name: mediamtx-container
        image: bluenviron/mediamtx:latest-rpi
        env:
        - name: MTX_PROTOCOLS
          value: "tcp"
        - name: MTX_PATHS_UNICAST_SOURCE
          value: "rpiCamera"
        - name: MTX_PATHDEFAULTS_RPICAMERAWIDTH
          value: "640"
        - name: MTX_PATHDEFAULTS_RPICAMERAHEIGHT
          value: "480"
        - name: MTX_PATHDEFAULTS_RPICAMERAFPS
          value: "10"
        securityContext:
          privileged: true
        volumeMounts:
        - mountPath: /run/udev
          name: udev
          readOnly: true
        - mountPath: /dev/shm
          name: shm-volume
          readOnly: false
        ports:
        - containerPort: 8554    # still declared for clarity
          name: rtsp
      volumes:
      - name: udev
        hostPath:
          path: /run/udev
      - name: shm-volume
        emptyDir:
          medium: Memory
 
---
apiVersion: v1
kind: Service
metadata:
  name: mediamtx-service
spec:
  ports:
    - name: rtsp
      port: 8554
      protocol: TCP
      targetPort: 8554
      nodePort: 30000
  selector:
    app: mediamtx
  type: NodePort
 ```


To deploy the server:
```bash
kubectl apply -f mediamtx-daemonset.yaml
```


Check the status of the deployment and the running pods:
```bash
kubectl get deployments -o wide
kubectl get pods -o wide
```
