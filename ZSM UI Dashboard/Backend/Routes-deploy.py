# routes/deploy.py
from fastapi import APIRouter, HTTPException
import paramiko
import asyncio
import sqlite3
import logging
import time
import os
from kubernetes import client, config

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BACKEND_DIR, 'iot_nodes.db')

# Load Kubernetes config
try:
    config.load_kube_config()
    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
except:
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()

def run_ssh_command(ip: str, username: str, password: str, command: str):
    """Execute SSH command on target node"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password, timeout=30)

        stdin, stdout, stderr = ssh.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        error = stderr.read().decode()

        ssh.close()

        return {"success": exit_code == 0, "output": output, "error": error}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/deploy/iot-setup")
async def deploy_to_all_iot_nodes():
    """ONE-CLICK Complete IoT Setup: Docker + K3s + MediaMTX + MyApp"""
    try:
        # 1. Get all IoT nodes from database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name, ip_address, ssh_username, ssh_password FROM iot_nodes")
        nodes = cursor.fetchall()
        conn.close()

        logger.info(f"Found {len(nodes)} IoT nodes for deployment")

        if not nodes:
            return {"success": False, "message": "No IoT nodes found in database"}

        results = {}
        master_ip = os.getenv("MASTER_NODE_IP", "192.168.0.147")
        k3s_token = os.getenv("K3S_TOKEN", "K101359ca9c5e83d0d1ad3d1991ddaa878b2531c304de905528a9a8e9f3fb372ff4::server:e55c9d718cfb81159eab206b13986e8a")

        # 2. Deployment scripts for each node
        deployment_scripts = {
            "1_install_docker": """
                echo "=== INSTALLING DOCKER ==="
                if command -v docker &> /dev/null; then
                    echo "Docker already installed"
                else
                    curl -fsSL https://get.docker.com -o get-docker.sh
                    sudo sh get-docker.sh
                    sudo usermod -aG docker $USER
                    echo "Docker installed successfully"
                fi
            """,

            "2_join_kubernetes": f"""
                echo "=== JOINING KUBERNETES CLUSTER ==="
                if command -v k3s &> /dev/null; then
                    echo "Already joined Kubernetes cluster"
                else
                    curl -sfL https://get.k3s.io | \\
                    K3S_TOKEN="{k3s_token}" \\
                    K3S_URL="https://{master_ip}:6443" \\
                    K3S_NODE_NAME="$(hostname)" \\
                    INSTALL_K3S_EXEC="agent --node-label role=iot" \\
                    sh -
                    echo "Joined Kubernetes cluster as $(hostname)"
                fi
            """,

            "3_deploy_mediamtx": """
                echo "=== DEPLOYING MEDIAMTX ==="
                sudo docker pull bluenviron/mediamtx:latest-rpi
                sudo docker stop mediamtx 2>/dev/null || true
                sudo docker rm mediamtx 2>/dev/null || true
                sudo docker run -d \\
                    --name mediamtx \\
                    --network host \\
                    --restart unless-stopped \\
                    --privileged \\
                    -v /run/udev:/run/udev:ro \\
                    -e MTX_PROTOCOLS=tcp \\
                    -e MTX_PATHS_UNICAST_SOURCE=rpiCamera \\
                    -e MTX_PATHDEFAULTS_RPICAMERAWIDTH=640 \\
                    -e MTX_PATHDEFAULTS_RPICAMERAHEIGHT=480 \\
                    -e MTX_PATHDEFAULTS_RPICAMERAFPS=10 \\
                    bluenviron/mediamtx:latest-rpi
                echo "✓ MediaMTX deployed and running"
            """
        }

        # 3. Execute deployment on each node
        for node in nodes:
            node_name, ip, username, password = node
            node_results = []

            logger.info(f"Deploying to node: {node_name} ({ip})")
            
            for step_name, script in deployment_scripts.items():
                logger.info(f"Executing {step_name} on {node_name}")

                result = await asyncio.get_event_loop().run_in_executor(
                    None, run_ssh_command, ip, username, password, script
                )

                node_results.append({
                    "step": step_name.replace("_", " ").title(),
                    "success": result["success"],
                    "message": result["output"] if result["success"] else result["error"]
                })

                # Brief pause between steps
                await asyncio.sleep(3)

            results[node_name] = node_results
        
        # 4. Wait for nodes to join Kubernetes
        logger.info("Waiting for nodes to join Kubernetes cluster...")
        await asyncio.sleep(20)

        # 5. Deploy Kubernetes applications
        k8s_results = await deploy_kubernetes_apps(nodes)

        return {
            "success": True,
            "message": "IoT deployment completed successfully!",
            "deployment_id": f"dep_{int(time.time())}",
            "nodes_processed": len(nodes),
            "node_results": results,
            "kubernetes_results": k8s_results,
            "camera_streams": [f"rtsp://{node[0]}:8554/unicast" for node in nodes]
        }

    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        return {"success": False, "message": f"Deployment error: {str(e)}"}

async def deploy_kubernetes_apps(nodes):
    """Deploy MediaMTX DaemonSet and MyApp StatefulSet"""
    try:
        results = {}

        # 1. Create ConfigMap with RTSP endpoints
        endpoints_data = {}
        for i, node in enumerate(nodes):
            endpoints_data[str(i)] = f"rtsp://{node[0]}:8554/unicast"

        configmap = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": "mediamtx-endpoints"},
            "data": endpoints_data
        }

        try:
            v1.create_namespaced_config_map(namespace="default", body=configmap)
            results["configmap"] = "Created mediamtx-endpoints ConfigMap"
        except:
            v1.patch_namespaced_config_map(name="mediamtx-endpoints", namespace="default", body=configmap)
            results["configmap"] = "Updated mediamtx-endpoints ConfigMap"

        # 2. Create MediaMTX DaemonSet
        mediamtx_daemonset = {
            "apiVersion": "apps/v1",
            "kind": "DaemonSet",
            "metadata": {"name": "mediamtx"},
            "spec": {
                "selector": {"matchLabels": {"app": "mediamtx"}},
                "template": {
                    "metadata": {"labels": {"app": "mediamtx"}},
                    "spec": {
                        "hostNetwork": True,
                        "nodeSelector": {"role": "iot"},
                        "containers": [{
                            "name": "mediamtx",
                            "image": "bluenviron/mediamtx:latest-rpi",
                            "env": [
                                {"name": "MTX_PROTOCOLS", "value": "tcp"},
                                {"name": "MTX_PATHS_UNICAST_SOURCE", "value": "rpiCamera"},
                                {"name": "MTX_PATHDEFAULTS_RPICAMERAWIDTH", "value": "640"},
                                {"name": "MTX_PATHDEFAULTS_RPICAMERAHEIGHT", "value": "480"},
                                {"name": "MTX_PATHDEFAULTS_RPICAMERAFPS", "value": "10"}
                            ],
                            "securityContext": {"privileged": True},
                            "volumeMounts": [{"mountPath": "/run/udev", "name": "udev", "readOnly": True}],
                            "ports": [{"containerPort": 8554, "name": "rtsp"}]
                        }],
                        "volumes": [{"name": "udev", "hostPath": {"path": "/run/udev"}}]
                    }
                }
            }
        }

        try:
            apps_v1.create_namespaced_daemon_set(namespace="default", body=mediamtx_daemonset)
            results["mediamtx"] = "Created MediaMTX DaemonSet"
        except:
            apps_v1.patch_namespaced_daemon_set(name="mediamtx", namespace="default", body=mediamtx_daemonset)
            results["mediamtx"] = "Updated MediaMTX DaemonSet"
        
        # 3. Create MyApp StatefulSet (Object Detection)
        myapp_statefulset = {
            "apiVersion": "apps/v1",
            "kind": "StatefulSet",
            "metadata": {"name": "myapp"},
            "spec": {
                "serviceName": "myapp",
                "replicas": len(nodes),
                "selector": {"matchLabels": {"app": "myapp"}},
                "template": {
                    "metadata": {"labels": {"app": "myapp"}},
                    "spec": {
                        "nodeSelector": {"role": "iot"},
                        "containers": [{
                            "name": "myapp",
                            "image": "siong23/classify-detect:latest",
                            "securityContext": {"privileged": True},
                            "env": [{
                                "name": "RTSP_ENDPOINT",
                                "valueFrom": {"configMapKeyRef": {"name": "mediamtx-endpoints", "key": "0"}}
                            }],
                            "command": ["python3", "detect.py", "--url", "rtsp://$(hostname):8554/unicast"],
                            "volumeMounts": [
                                {"name": "dev-vchiq", "mountPath": "/dev/vchiq"},
                                {"name": "dev-bus-usb", "mountPath": "/dev/bus/usb"}
                            ]
                        }],
                        "volumes": [
                            {"name": "dev-vchiq", "hostPath": {"path": "/dev/vchiq"}},
                            {"name": "dev-bus-usb", "hostPath": {"path": "/dev/bus/usb"}}
                        ]
                    }
                }
            }
        }
        
        try:
            apps_v1.create_namespaced_stateful_set(namespace="default", body=myapp_statefulset)
            results["myapp"] = "Created MyApp StatefulSet"
        except:
            apps_v1.patch_namespaced_stateful_set(name="myapp", namespace="default", body=myapp_statefulset)
            results["myapp"] = "Updated MyApp StatefulSet"

        return results

    except Exception as e:
        return {"error": f"Kubernetes deployment failed: {str(e)}"}

@router.get("/deploy/status")
async def get_deployment_status():
    """Check deployment status"""
    return {
        "status": "ready", 
        "timestamp": time.time(),
        "message": "Deployment system is operational"
    }
