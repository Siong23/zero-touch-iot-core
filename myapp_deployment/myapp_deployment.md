Create myapp-deploy.yaml:
```bash
nano myapp-deploy.yaml
```


Deploy the myapp-deploy.yaml:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-deployment
  labels:
    app: myapp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      nodeSelector:
        kubernetes.io/hostname: <device-name> ##iot
      containers:
      - env:
        - name: DISPLAY
          value: :0
        - name: LD_LIBRARY_PATH
          value: /opt/vc/lib:/lib:/usr/lib:/usr/local/lib
        name: myapp
        image: siong23/classify-detect:latest
        imagePullPolicy: IfNotPresent
        securityContext:
          privileged: true
        volumeMounts:
        - mountPath: /dev/vchiq
          name: dev-vchiq
        - mountPath: /dev/bus/usb
          name: dev-bus-usb
        - mountPath: /dev/vc
          name: dev-vc
        - mountPath: /dev/video0
          name: dev-video0
        - mountPath: /tmp/.X11-unix
          name: tmp-x11-unix
        - mountPath: /home/user/.Xauthority
          name: xauthority
        - mountPath: /coral/examples-camera/opencv/detect.py
          name: config-volume
          subPath: detect.py
#       command: ["tail","-f","/dev/null"]
#       command: ["/bin/bash"]
      volumes:
      - name: dev-vchiq
        hostPath:
          path: /dev/vchiq
      - name: dev-bus-usb
        hostPath:
          path: /dev/bus/usb
      - name: dev-vc
        hostPath:
          path: /dev/vc
      - name: dev-video0
        hostPath:
          path: /dev/video0
      - name: tmp-x11-unix
        hostPath:
          path: /tmp/.X11-unix
      - name: xauthority
        hostPath:
          path: /home/pi/.Xauthority
      - name: config-volume
        configMap:
          name: myapp-config
#      hostNetwork: true
#      dnsPolicy: ClusterFirstWithHostNet
 ```


To deploy the app:
```bash
kubectl apply -f myapp-deploy.yaml
```


Check the status of the deployment and the running pods:
```bash
kubectl get deployments -o wide
kubectl get pods -o wide
```
