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
