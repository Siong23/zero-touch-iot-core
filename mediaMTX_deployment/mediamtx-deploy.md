Deploy the mediamtx_deploy.yaml:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mediamtx-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mediamtx
  template:
    metadata:
      labels:
        app: mediamtx
    spec:
      nodeSelector:
        kubernetes.io/hostname: iot 
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
        - containerPort: 8554
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
bectl apply -f mediamtx-deploy.yaml
```


Check the status of the deployment and the running pods:
```bash
kubectl get deployments -o wide
kubectl get pods -o wide
```
