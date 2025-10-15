###main.py
from fastapi.responses import JSONResponse  
from fastapi import FastAPI, HTTPException, Depends, status, Request, Body, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from kubernetes import client, config
from prometheus_client import generate_latest, Gauge
import json
import yaml
import subprocess
import paramiko
import logging
import os
import random
import requests
import asyncio
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
import sqlite3
import shutil  # For file copying
import time  # For retry delays

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Edge Computing Management API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (you can restrict this later)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods including OPTIONS
    allow_headers=["*"],  # Allow all headers including Authorization
    expose_headers=["*"], # Expose all headers to the frontend
)

#WEBSOCKET PROGRESS MANAGER
class ProgressManager:
    def __init__(self):
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Progress WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Progress WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_progress(self, progress_data: dict):
        logger.info(f"📊 Sending WebSocket progress: {progress_data}")  # Debug logging
        
        if not self.active_connections:
            logger.warning("No active WebSocket connections")
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(progress_data)
                logger.info(f"✅ Progress sent successfully to WebSocket")
            except Exception as e:
                logger.error(f"❌ Failed to send progress update: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

# Global progress manager instance
progress_manager = ProgressManager()

# WebSocket endpoint for progress updates
@app.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    await progress_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive by receiving messages
            data = await websocket.receive_text()
            logger.info(f"WebSocket received: {data}")
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
        progress_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        progress_manager.disconnect(websocket)

# Security setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('nodes.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS nodes
                 (name TEXT PRIMARY KEY, 
                  ip TEXT, 
                  username TEXT, 
                  password TEXT, 
                  type TEXT,
                  is_master BOOLEAN DEFAULT 0)''')
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

# Call init_db when the app starts
init_db()

# Master node configuration (hardcoded as per planning)
MASTER_NAME = "nuc2"
MASTER_IP = "192.168.0.147"  # Update if dynamic

# Files directory (assume files are here)
FILES_DIR = os.path.join(os.path.dirname(__file__), 'files')
FILES_TO_COPY = [
    'offloading_manager.py', 'q_learning_model.pkl', 'mediamtx-daemonset.yaml',
    'myapp.yaml', 'configmap-mediamtx-endpoints.yaml', 'offloading-manager-pod.yaml',
    'detect.py'
]  # /etc/rancher/k3s/k3s.yaml is generated, not copied

# Load Kubernetes config (after deployment, it will be available)
try:
    config.load_kube_config(config_file=os.getenv("KUBECONFIG_PATH"))
    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    logger.info("Successfully loaded Kubernetes config")
except Exception as e:
    logger.warning(f"Kubernetes config not loaded yet: {e}. Will load after deployment.")

# Prometheus metrics
CPU_GAUGE = Gauge('node_cpu_usage', 'CPU usage percentage', ['node', 'role'])
MEMORY_GAUGE = Gauge('node_memory_usage', 'Memory usage percentage', ['node', 'role'])
NODE_STATUS_GAUGE = Gauge('node_status', 'Node status (1=online, 0=offline)', ['node', 'role'])

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    role: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

class NodeCreationRequest(BaseModel):
    node_type: str
    prefix: str
    count: int
    ssh_username: Optional[str] = None
    ssh_password: Optional[str] = None
    ssh_key: Optional[str] = None

# Mock user database (replace with real database in production)
fake_users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": pwd_context.hash("admin123"),
        "role": "admin",
        "disabled": False,
    }
}

def setup_files_directory():
    """Create files directory and validate required files"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(FILES_DIR, exist_ok=True)
        logger.info(f"Files directory created/verified: {FILES_DIR}")
        
        # Check for required files
        missing_files = []
        for file in FILES_TO_COPY:
            file_path = os.path.join(FILES_DIR, file)
            if not os.path.exists(file_path):
                missing_files.append(file)
                logger.error(f"Missing required file: {file}")
        
        if missing_files:
            raise HTTPException(
                status_code=500,
                detail=f"Missing required files: {', '.join(missing_files)}. Please add them to {FILES_DIR}"
            )
        
        logger.info("All required files are present")
        return True
        
    except Exception as e:
        logger.error(f"File directory setup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File setup failed: {str(e)}")

def get_installation_commands(node_type):
    """Get appropriate installation commands based on node type"""
    if node_type == "iot":  # Raspberry Pi
        return [
            "sudo apt-get update -y",
            "sudo apt-get install -y curl wget",
            "curl -fsSL https://get.docker.com -o get-docker.sh",
            "sudo sh get-docker.sh",
            "sudo usermod -aG docker $USER",
            "sudo apt-get install -y python3 python3-pip",
            "sudo systemctl enable docker",
            "sudo systemctl start docker",
        ]
    else:  # Edge nodes (Ubuntu)
        return [
            "sudo apt-get update -y",
            "sudo apt-get install -y ca-certificates curl wget",
            "sudo install -m 0755 -d /etc/apt/keyrings",
            "sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc",
            "sudo chmod a+r /etc/apt/keyrings/docker.asc",
            'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null',
            "sudo apt-get update -y",
            "sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin",
            "sudo usermod -aG docker $USER",
            "sudo apt install -y python3 python3-pip",
            "sudo systemctl enable docker",
            "sudo systemctl start docker",
        ]

def ssh_connect_with_retry(ip, username, password, retries=3, delay=10):
    """SSH connection with retry logic"""
    for attempt in range(retries):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=username, password=password, timeout=30)
            logger.info(f"SSH connection successful to {ip} on attempt {attempt + 1}")
            return ssh
        except Exception as e:
            logger.warning(f"SSH connection attempt {attempt + 1} failed to {ip}: {str(e)}")
            if attempt < retries - 1:
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                raise e
    return None

def ssh_execute_with_retry(ssh, cmd, retries=2, delay=5):
    """Execute SSH command with retry logic"""
    last_error = ""
    for attempt in range(retries):
        try:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if exit_status == 0:
                logger.debug(f"Command successful: {cmd}")
                return exit_status, output, error
            
            last_error = error
            logger.warning(f"Command failed (attempt {attempt + 1}): {cmd}. Error: {error}")
            
            if attempt < retries - 1:
                time.sleep(delay)
                
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Command execution failed (attempt {attempt + 1}): {cmd}. Error: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    
    return exit_status, "", last_error

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Helper functions for node data
def get_node_ip(node):
    """Extract node IP address from node status"""
    for address in node.status.addresses:
        if address.type == "InternalIP":
            return address.address
    return "N/A"

def get_node_memory(node):
    """Extract node memory information"""
    if node.status.allocatable and 'memory' in node.status.allocatable:
        # Convert memory from bytes to MB for readability
        memory_bytes = int(node.status.allocatable['memory'].replace('Ki', '')) * 1024
        memory_mb = memory_bytes / (1024 * 1024)
        return f"{int(memory_mb)} MB"
    return "N/A"

async def get_real_cpu_usage(node_name):
    """Get real CPU utilization from Prometheus using node labels"""
    try:
        prometheus_url = "http://localhost:9090/api/v1/query"

        # Method 1: Try with node label (cleanest approach)
        query = f'100 - (avg by (node) (irate(node_cpu_seconds_total{{mode="idle", node="{node_name}"}}[5m])) * 100)'

        response = requests.get(prometheus_url, params={"query": query}, timeout=5)
        data = response.json()
        
        if (data["status"] == "success" and data["data"]["result"]):
            cpu_usage = float(data["data"]["result"][0]["value"][1])
            return f"{cpu_usage:.1f}%"

        # Method 2: Fallback - try to find the node by IP
        nodes = v1.list_node()
        for node in nodes.items:
            if node.metadata.name == node_name:
                node_ip = get_node_ip(node)
                if node_ip and node_ip != "N/A":
                    query = f'100 - (avg by (instance) (irate(node_cpu_seconds_total{{mode="idle", instance=~".*{node_ip}.*"}}[5m])) * 100)'
                    response = requests.get(prometheus_url, params={"query": query}, timeout=5)
                    data = response.json()
                    if (data["status"] == "success" and data["data"]["result"]):
                        cpu_usage = float(data["data"]["result"][0]["value"][1])
                        return f"{cpu_usage:.1f}%"
                break

        return "0%"  # No data found
        
    except Exception as e:
        logger.error(f"Error getting CPU usage for {node_name}: {e}")
        return "0%"

# SSH Helper Functions
def ssh_join_node_generic(ip, username, password, master_ip, token, node_name, role):
    try:
        ssh = ssh_connect_with_retry(ip, username, password)
        if not ssh:
            return {"success": False, "error": f"Failed to connect to {ip} after multiple attempts"}
        
        logger.info(f"Checking for existing k3s installation on {node_name}...")
        check_cmd = "which k3s-agent || echo 'not-installed'"
        exit_status, output, error = ssh_execute_with_retry(ssh, check_cmd)
        existing_install = output.strip()
        
        if existing_install != "not-installed":
            logger.info(f"Found existing k3s installation on {node_name}, removing...")
            cleanup_cmd = "sudo /usr/local/bin/k3s-agent-uninstall.sh"
            ssh_execute_with_retry(ssh, cleanup_cmd)
            # Additional cleanup
            ssh_execute_with_retry(ssh, "sudo rm -rf /etc/rancher /var/lib/rancher /var/lib/kubelet")
        
        # Join the cluster with role
        logger.info(f"Installing k3s agent and joining cluster as {role} node {node_name}...")
        join_cmd = f"""sudo curl -sfL https://get.k3s.io | \
        K3S_TOKEN="{token}" \
        K3S_URL="https://{master_ip}:6443" \
        K3S_NODE_NAME="{node_name}" \
        INSTALL_K3S_EXEC="agent --node-label role={role} --node-label name={node_name}" \
        sh -"""
        
        exit_status, output, error = ssh_execute_with_retry(ssh, join_cmd)
        ssh.close()

        if exit_status == 0:
            logger.info(f"Successfully joined {role} node {node_name} to cluster")
            return {
                "success": True, 
                "message": f"{role.capitalize()} node {node_name} joined cluster successfully",
                "output": output
            }
        else:
            logger.error(f"Failed to join {role} node {node_name}. Exit status: {exit_status}, Error: {error}")
            return {
                "success": False, 
                "error": f"Exit code {exit_status}: {error}"
            }

    except Exception as e:
        error_msg = f"Unexpected error joining {node_name}: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

# delete iot nodes
def ssh_remove_node(ip, username, password, node_name):
    try:
        ssh = ssh_connect_with_retry(ip, username, password)
        if not ssh:
            return {"success": False, "error": f"Failed to connect to {ip}"}

        # Remove k3s agent
        remove_cmd = "sudo /usr/local/bin/k3s-agent-uninstall.sh"
        exit_status, output, error = ssh_execute_with_retry(ssh, remove_cmd)

        ssh.close()

        if exit_status == 0:
            return {"success": True, "message": f"Node {node_name} removed from cluster", "output": output}
        else:
            return {"success": False, "error": error}

    except Exception as e:
        return {"success": False, "error": str(e)}

# API Routes 
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=float(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.get("/")
async def root():
    return {"message": "Edge Computing Management API"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Server is running"}

# Updated Get Edge Nodes: Merge DB (pending) and K8s
@app.get("/api/edge-nodes", response_model=List[dict])
async def get_edge_nodes(current_user: User = Depends(get_current_active_user)):
    try:
        # Get from K8s if available
        k8s_nodes_dict = {}
        try:
            nodes = v1.list_node()
            for node in nodes.items:
                node_name = node.metadata.name
                if "nuc" in node_name.lower() or "lim" in node_name.lower():
                    status = "offline"
                    for condition in node.status.conditions:
                        if condition.type == "Ready":
                            status = "online" if condition.status == "True" else "offline"
                            break
                    cpu_usage = await get_real_cpu_usage(node_name)
                    k8s_nodes_dict[node_name] = {
                        "name": node_name,
                        "ip": get_node_ip(node),
                        "status": status,
                        "cpu": cpu_usage,
                        "memory": get_node_memory(node)
                    }
        except Exception as e:
            logger.warning(f"K8s not available yet: {e}")

        # Get from DB
        conn = sqlite3.connect('nodes.db')
        c = conn.cursor()
        c.execute("SELECT name, ip FROM nodes WHERE type='edge'")
        db_edges = {row[0]: {"name": row[0], "ip": row[1], "status": "pending", "cpu": "N/A", "memory": "N/A"} for row in c.fetchall()}
        conn.close()

        # Merge: K8s overrides DB
        merged = {**db_edges, **k8s_nodes_dict}

        return list(merged.values())
    except Exception as e:
        logger.error(f"Error getting edge nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Updated Get IoT Nodes:
@app.get("/api/iot-nodes", response_model=List[dict])
async def get_iot_nodes(current_user: User = Depends(get_current_active_user)):
    try:
        # Get from K8s if available
        k8s_nodes_dict = {}
        try:
            nodes = v1.list_node()
            for node in nodes.items:
                node_name = node.metadata.name
                if "iot" in node_name.lower() or "rpi" in node_name.lower():
                    status = "offline"
                    for condition in node.status.conditions:
                        if condition.type == "Ready":
                            status = "online" if condition.status == "True" else "offline"
                            break
                    # Get REAL CPU usage from Prometheus
                    cpu_usage = await get_real_cpu_usage(node_name)
                    k8s_nodes_dict[node_name] = {
                        "name": node_name,
                        "ip": get_node_ip(node),
                        "status": status,
                        "cpu": cpu_usage,
                        "memory": get_node_memory(node)
                    }
        except Exception as e:
            logger.warning(f"K8s not available yet: {e}")

        # Get from DB
        conn = sqlite3.connect('nodes.db')
        c = conn.cursor()
        c.execute("SELECT name, ip FROM nodes WHERE type='iot'")
        db_iots = {row[0]: {"name": row[0], "ip": row[1], "status": "pending", "cpu": "N/A", "memory": "N/A"} for row in c.fetchall()}
        conn.close()

        # Merge: K8s overrides DB
        merged = {**db_iots, **k8s_nodes_dict}

        return list(merged.values())
    except Exception as e:
        logger.error(f"Error getting IoT nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/nodes")
async def get_nodes(current_user: User = Depends(get_current_active_user)):
    try:
        nodes = v1.list_node()
        node_data = []

        for node in nodes.items:
            node_name = node.metadata.name
            labels = node.metadata.labels or {}
            role = labels.get('role', 'unknown')

            # Get node status
            status = "Unknown"
            for condition in node.status.conditions:
                if condition.type == "Ready":
                    status = "Online" if condition.status == "True" else "Offline"
                    break

            # Get node addresses
            addresses = {}
            for addr in node.status.addresses:
                addresses[addr.type] = addr.address

            # Get resource information
            capacity = node.status.capacity or {}
            allocatable = node.status.allocatable or {}

            node_data.append({
                "name": node_name,
                "role": role,
                "status": status,
                "addresses": addresses,
                "labels": labels,
                "capacity": {
                    "cpu": capacity.get('cpu', 'N/A'),
                    "memory": capacity.get('memory', 'N/A'),
                    "pods": capacity.get('pods', 'N/A')
                },
                "allocatable": {
                    "cpu": allocatable.get('cpu', 'N/A'),
                    "memory": allocatable.get('memory', 'N/A'),
                    "pods": allocatable.get('pods', 'N/A')
                }
            })

        return {"nodes": node_data}
    except Exception as e:
        logger.error(f"Error getting nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pods")
async def get_pods(current_user: User = Depends(get_current_active_user)):
    try:
        pods = v1.list_pod_for_all_namespaces(watch=False)
        pod_data = []

        for pod in pods.items:
            pod_data.append({
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "node": pod.spec.node_name,
                "status": pod.status.phase,
                "ip": pod.status.pod_ip,
                "created": pod.metadata.creation_timestamp,
                "labels": pod.metadata.labels or {}
            })        
        return {"pods": pod_data}
    except Exception as e:
        logger.error(f"Error getting pods: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/deployments")
async def get_deployments(current_user: User = Depends(get_current_active_user)):
    try:
        deployments = apps_v1.list_deployment_for_all_namespaces(watch=False)
        deployment_data = []

        for deployment in deployments.items:
            deployment_data.append({
                "name": deployment.metadata.name,
                "namespace": deployment.metadata.namespace,
                "replicas": deployment.status.replicas if deployment.status.replicas else 0,
                "available": deployment.status.available_replicas if deployment.status.available_replicas else 0,
                "ready": deployment.status.ready_replicas if deployment.status.ready_replicas else 0
            })

        return {"deployments": deployment_data}
    except Exception as e:
        logger.error(f"Error getting deployments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

##add iot nodes
@app.post("/api/nodes/add")
async def add_node(data: dict = Body(...), current_user: User = Depends(get_current_active_user)):
    """Add a new IoT node to DB (pending, join during deploy)"""
    try:
        name = data.get("name")
        ip = data.get("ip")
        username = data.get("ssh_username")
        password = data.get("ssh_password")

        logger.info(f"Received request to add node: {name} at {ip}")

        if not name or not ip or not username or not password:
            raise HTTPException(status_code=400, detail="Name, IP, SSH username and password are required")

        # Validate IP address format
        import re
        ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
        if not ip_pattern.match(ip):
            raise HTTPException(status_code=400, detail="Invalid IP address format")

        # Store in DB
        conn = sqlite3.connect('nodes.db')
        c = conn.cursor()
        
        # FIXED: Include is_master column (default to 0 for IoT nodes)
        c.execute("INSERT OR REPLACE INTO nodes (name, ip, username, password, type, is_master) VALUES (?, ?, ?, ?, ?, ?)", 
                 (name, ip, username, password, 'iot', 0))
        conn.commit()
        conn.close()

        logger.info(f"Successfully added pending IoT node {name}")
        return {
            "message": f"IoT node {name} added as pending. Use 'Deploy to All Nodes' to join cluster.",
            "success": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in add_node: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

##add edge
@app.post("/api/edge-nodes/add")
async def add_edge_node(data: dict = Body(...), current_user: User = Depends(get_current_active_user)):
    """Add a new Edge node to DB (pending, join during deploy)"""
    try:
        name = data.get("name")
        ip = data.get("ip")
        username = data.get("ssh_username")
        password = data.get("ssh_password")
        is_master = data.get("is_master", False)  # Get master flag from frontend

        logger.info(f"Received request to add edge node: {name} at {ip} (master: {is_master})")

        if not name or not ip or not username or not password:
            raise HTTPException(status_code=400, detail="Name, IP, SSH username and password are required")

        # Validate IP address format
        import re
        ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
        if not ip_pattern.match(ip):
            raise HTTPException(status_code=400, detail="Invalid IP address format")

        # Store in DB
        conn = sqlite3.connect('nodes.db')
        c = conn.cursor()
        
        # First, update database schema if needed (add is_master column)
        try:
            c.execute("SELECT is_master FROM nodes LIMIT 1")
        except sqlite3.OperationalError:
            # Column doesn't exist, alter table
            logger.info("Adding is_master column to nodes table")
            c.execute("ALTER TABLE nodes ADD COLUMN is_master BOOLEAN DEFAULT 0")
        
        # If setting as master, clear existing master
        if is_master:
            logger.info(f"Setting {name} as master node - clearing previous master")
            c.execute("UPDATE nodes SET is_master = 0 WHERE is_master = 1")
        
        # Store node with master flag
        c.execute("INSERT OR REPLACE INTO nodes (name, ip, username, password, type, is_master) VALUES (?, ?, ?, ?, ?, ?)", 
                 (name, ip, username, password, 'edge', is_master))
        conn.commit()
        conn.close()

        message = f"Edge node {name} added as pending. Use 'Deploy to All Nodes' to join cluster."
        if is_master:
            message += " (Set as Master Node)"
        
        logger.info(f"Successfully added pending edge node {name} (master: {is_master})")
        return {
            "message": message,
            "success": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in add_edge_node: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.delete("/api/nodes/{node_name}")
async def delete_node(node_name: str, current_user: User = Depends(get_current_active_user)):
    """Remove a node from the cluster and DB"""
    try:
        # SECURITY: Prevent deletion of master node
        if node_name == MASTER_NAME:
            raise HTTPException(
                status_code=403, 
                detail=f"Cannot delete master node: {node_name}"
            )
        
        # Get node from DB for SSH details
        conn = sqlite3.connect('nodes.db')
        c = conn.cursor()
        c.execute("SELECT ip, username, password FROM nodes WHERE name=?", (node_name,))
        node_data = c.fetchone()
        conn.close()

        if node_data:
            ip, username, password = node_data
            # Remove via SSH if joined
            result = ssh_remove_node(ip, username, password, node_name)
            if not result["success"]:
                logger.warning(f"Failed to remove node via SSH: {result['error']}")

        # Drain and delete from K8s
        try:
            drain_cmd = ["kubectl", "drain", node_name, "--ignore-daemonsets", "--delete-emptydir-data", "--force"]
            drain_result = subprocess.run(drain_cmd, capture_output=True, text=True)
            if drain_result.returncode != 0:
                logger.warning(f"Failed to drain node {node_name}: {drain_result.stderr}")

            delete_cmd = ["kubectl", "delete", "node", node_name]
            delete_result = subprocess.run(delete_cmd, capture_output=True, text=True)
            if delete_result.returncode != 0:
                logger.warning(f"Failed to delete node {node_name}: {delete_result.stderr}")
        except Exception as e:
            logger.warning(f"K8s node deletion failed: {e}")

        # Remove from DB
        conn = sqlite3.connect('nodes.db')
        c = conn.cursor()
        c.execute("DELETE FROM nodes WHERE name=?", (node_name,))
        conn.commit()
        conn.close()

        return {"message": f"Node {node_name} removed successfully", "success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting node {node_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

## Deploy to All Nodes
@app.post("/api/deploy/all")
async def deploy_all(current_user: User = Depends(get_current_active_user)):
    """Automated deployment: Install on master, join nodes, deploy apps"""
    try:
        # Send initial progress
        await progress_manager.send_progress({
            "type": "progress",
            "percent": 10,
            "message": "Starting deployment...",
            "active_step": "step-master"
        })

        # SMART CHECK: See what's already deployed
        existing_nodes = []
        try:
            config.load_kube_config(config_file="/home/nuc2/.kube/config")
            v1 = client.CoreV1Api()
            existing_nodes = [node.metadata.name for node in v1.list_node().items]
            await progress_manager.send_progress({
                "type": "progress",
                "percent": 15,
                "message": f"Found {len(existing_nodes)} existing nodes in cluster: {', '.join(existing_nodes)}"
            })
            logger.info(f"Found {len(existing_nodes)} existing nodes: {existing_nodes}")
        except Exception as e:
            logger.warning(f"Could not check existing cluster: {e}")
            # Continue with full deployment

        # Step 0: Validate prerequisites
        await progress_manager.send_progress({
            "type": "progress", 
            "percent": 20,
            "message": "Validating prerequisites..."
        })
        setup_files_directory()
        validate_deployment_files()  

        # Check if nodes exist in database
        conn = sqlite3.connect('nodes.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM nodes")
        node_count = c.fetchone()[0]
        conn.close()
        
        if node_count == 0:
            await progress_manager.send_progress({
                "type": "error",
                "message": "No nodes found in database",
                "percent": 0
            })
            raise HTTPException(
                status_code=400, 
                detail="No nodes found in database. Please add nodes first."
            )
        
        await progress_manager.send_progress({
            "type": "progress",
            "percent": 25,
            "message": f"Found {node_count} nodes in database"
        })
        logger.info(f"Found {node_count} nodes in database")

        # === DYNAMIC MASTER NODE LOOKUP ===
        await progress_manager.send_progress({
            "type": "progress",
            "percent": 30,
            "message": "Identifying master node..."
        })
        # Get master node dynamically from database
        master_node = get_master_node()
        if not master_node:
            await progress_manager.send_progress({
                "type": "error",
                "message": "No master node defined",
                "percent": 0
            })
            raise HTTPException(
                status_code=400, 
                detail="No master node defined. Please set a master node first."
            )
        
        MASTER_NAME = master_node["name"]
        MASTER_IP = master_node["ip"]
        MASTER_USERNAME = master_node["username"]
        MASTER_PASSWORD = master_node["password"]
        
        await progress_manager.send_progress({
            "type": "progress",
            "percent": 35,
            "message": f"Using master node: {MASTER_NAME} at {MASTER_IP}"
        })
        logger.info(f"Using master node: {MASTER_NAME} at {MASTER_IP}")
        # === END DYNAMIC MASTER LOOKUP ===

        # SMART CHECK: Skip master setup if already running
        k3s_running = False
        try:
            result = subprocess.run(["sudo", "systemctl", "is-active", "k3s"], 
                                  capture_output=True, text=True)
            k3s_running = result.returncode == 0
        except:
            pass

        if k3s_running and MASTER_NAME in existing_nodes:
            await progress_manager.send_progress({
                "type": "progress",
                "percent": 50,
                "message": "Master node already setup, skipping installation..."
            })
            logger.info("Master node already setup, skipping installation...")
            
            # Just ensure kubeconfig is loaded
            try:
                config.load_kube_config(config_file="/home/nuc2/.kube/config")
                v1 = client.CoreV1Api()
                apps_v1 = client.AppsV1Api()
            except Exception as e:
                logger.error(f"Failed to load kubeconfig: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to load kubeconfig: {e}")
        else:
            # Run full master setup
            await progress_manager.send_progress({
                "type": "progress",
                "percent": 40,
                "message": "Setting up master node..."
            })
            logger.info("Setting up master node...")

            # Use the pre-created script for k3s installation
            install_script_path = "/home/nuc2/install-k3s.sh"

            # First install k3s using our script
            await progress_manager.send_progress({
                "type": "progress",
                "percent": 45,
                "message": "Installing k3s on master node..."
            })
            logger.info("Installing k3s using custom script...")
            result = subprocess.run([install_script_path], shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                await progress_manager.send_progress({
                    "type": "error",
                    "message": f"k3s installation failed: {result.stderr}",
                    "percent": 0
                })
                logger.error(f"k3s installation failed: {result.stderr}")
                raise HTTPException(status_code=500, detail=f"k3s installation failed: {result.stderr}")
            else:
                await progress_manager.send_progress({
                    "type": "progress",
                    "percent": 50,
                    "message": "k3s installed successfully"
                })
                logger.info("k3s installed successfully")

            # Wait for k3s to be fully ready
            await progress_manager.send_progress({
                "type": "progress",
                "percent": 55,
                "message": "Waiting for k3s to be ready..."
            })
            logger.info("Waiting for k3s to be ready...")
            time.sleep(30)

            # Now load kubeconfig
            try:
                await progress_manager.send_progress({
                    "type": "progress",
                    "percent": 60,
                    "message": "Loading Kubernetes configuration..."
                })
                config.load_kube_config(config_file="/home/nuc2/.kube/config")
                v1 = client.CoreV1Api()
                apps_v1 = client.AppsV1Api()
                await progress_manager.send_progress({
                    "type": "progress",
                    "percent": 65,
                    "message": "Successfully loaded Kubernetes config"
                })
                logger.info("Successfully loaded Kubernetes config")
            except Exception as e:
                await progress_manager.send_progress({
                    "type": "error",
                    "message": f"Failed to load kubeconfig: {e}",
                    "percent": 0
                })
                logger.error(f"Failed to load kubeconfig: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to load kubeconfig: {e}")

            # Now install other components (non-critical, can fail)
            await progress_manager.send_progress({
                "type": "progress",
                "percent": 70,
                "message": "Installing additional components..."
            })
            other_components = [
                "sudo apt-get install -y python3 python3-pip",
                "curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash",
                "helm repo add prometheus-community https://prometheus-community.github.io/helm-charts",
                "helm repo update",
                "kubectl create namespace monitoring || true",
                "helm install prometheus-operator prometheus-community/kube-prometheus-stack --namespace monitoring --set grafana.service.type=NodePort --set prometheus.service.type=NodePort",
            ]

            for i, cmd in enumerate(other_components):
                progress = 70 + int((i / len(other_components)) * 5)
                await progress_manager.send_progress({
                    "type": "progress",
                    "percent": progress,
                    "message": f"Installing component {i+1}/{len(other_components)}..."
                })
                logger.info(f"Running: {cmd[:50]}...")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Command failed but continuing: {cmd}. Error: {result.stderr}")

            # Configure Grafana for embedding and set fixed NodePort
            await progress_manager.send_progress({
                "type": "progress", 
                "percent": 77,
                "message": "Configuring Grafana for dashboard embedding..."
            })

            grafana_setup_commands = [
                "kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana -n monitoring --timeout=300s",
                "kubectl patch deployment prometheus-operator-grafana -n monitoring -p '{\"spec\":{\"template\":{\"spec\":{\"containers\":[{\"name\":\"grafana\",\"env\":[{\"name\":\"GF_SECURITY_ALLOW_EMBEDDING\",\"value\":\"true\"},{\"name\":\"GF_AUTH_ANONYMOUS_ENABLED\",\"value\":\"true\"},{\"name\":\"GF_AUTH_ANONYMOUS_ORG_ROLE\",\"value\":\"Viewer\"}]}]}}}}'",
                "kubectl patch svc prometheus-operator-grafana -n monitoring -p '{\"spec\":{\"ports\":[{\"port\":80,\"nodePort\":32000}]}}'",
                "kubectl rollout restart deployment/prometheus-operator-grafana -n monitoring",
                "kubectl rollout status deployment/prometheus-operator-grafana -n monitoring --timeout=300s"
            ]

            for j, cmd in enumerate(grafana_setup_commands):
                progress = 77 + int((j / len(grafana_setup_commands)) * 3)
                await progress_manager.send_progress({
                    "type": "progress",
                    "percent": progress,
                    "message": f"Configuring Grafana {j+1}/{len(grafana_setup_commands)}..."
                })
                logger.info(f"Running Grafana setup: {cmd[:80]}...")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
                if result.returncode != 0:
                    logger.warning(f"Grafana setup command failed: {cmd}. Error: {result.stderr}")
                else:
                    logger.info(f"Grafana setup successful: {cmd[:50]}...")

            # Copy files to master home
            await progress_manager.send_progress({
                "type": "progress",
                "percent": 80,
                "message": "Copying application files to master..."
            })
            master_username = os.getenv("MASTER_USERNAME", "nuc2")
            target_dir = f"/home/{master_username}/"
            logger.info(f"Copying files to master: {target_dir}")
            
            for file in FILES_TO_COPY:
                src = os.path.join(FILES_DIR, file)
                if os.path.exists(src):
                    try:
                        shutil.copy(src, target_dir)
                        logger.info(f"Copied {file} to master")
                    except Exception as e:
                        logger.warning(f"Failed to copy {file}: {e}")
                else:
                    logger.warning(f"File {file} not found in {FILES_DIR}")

        # SMART: Only join missing nodes
        await progress_manager.send_progress({
            "type": "progress",
            "percent": 85,
            "message": "Checking which nodes need to join cluster...",
            "active_step": "step-workers"
        })

        # Retrieve token from accessible location
        token = None
        try:
            with open("/home/nuc2/node-token", "r") as f:
                token = f.read().strip()
            logger.info("Retrieved k3s join token from /home/nuc2/node-token")
        except Exception as e:
            logger.error(f"Failed to get token from /home/nuc2/node-token: {e}")
            # Fallback to system location
            try:
                result = subprocess.run(["sudo", "cat", "/var/lib/rancher/k3s/server/node-token"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    token = result.stdout.strip()
                    logger.info("Retrieved k3s token via subprocess")
            except Exception as e2:
                logger.error(f"All token retrieval methods failed: {e2}")

        if not token:
            await progress_manager.send_progress({
                "type": "error",
                "message": "Failed to get k3s join token",
                "percent": 0
            })
            raise HTTPException(status_code=500, detail="Failed to get k3s join token")

        # Get all worker nodes from database
        conn = sqlite3.connect('nodes.db')
        c = conn.cursor()
        c.execute("SELECT name, ip, username, password, type FROM nodes WHERE name != ?", (MASTER_NAME,))
        all_nodes = c.fetchall()
        conn.close()

        # Filter out nodes that are already in cluster
        nodes_to_join = []
        for node in all_nodes:
            name, ip, username, password, node_type = node
            if name not in existing_nodes:
                nodes_to_join.append(node)
                await progress_manager.send_progress({
                    "type": "progress",
                    "percent": 86,
                    "message": f"Node {name} needs to join cluster"
                })
                logger.info(f"Node {name} needs to join cluster")
            else:
                await progress_manager.send_progress({
                    "type": "progress", 
                    "percent": 86,
                    "message": f"Node {name} already in cluster, skipping"
                })
                logger.info(f"Node {name} already in cluster, skipping")

        if not nodes_to_join:
            await progress_manager.send_progress({
                "type": "progress",
                "percent": 90,
                "message": "All nodes already joined cluster, skipping node joining"
            })
            logger.info("All nodes already joined cluster, skipping node joining")
        else:
            await progress_manager.send_progress({
                "type": "progress",
                "percent": 87,
                "message": f"Joining {len(nodes_to_join)} new nodes to cluster..."
            })
            logger.info(f"Joining {len(nodes_to_join)} new nodes to cluster...")
            
            for i, (name, ip, username, password, node_type) in enumerate(nodes_to_join):
                progress = 87 + int((i / len(nodes_to_join)) * 8)
                await progress_manager.send_progress({
                    "type": "progress",
                    "percent": progress,
                    "message": f"Setting up {name} ({ip}) as {node_type}"
                })
                logger.info(f"Setting up node: {name} ({ip}) as {node_type}")
                
                try:
                    ssh = ssh_connect_with_retry(ip, username, password)
                    if not ssh:
                        raise Exception(f"Failed to connect to {name}")

                    # Install prerequisites based on node type
                    prereq_cmds = get_installation_commands(node_type)
                    logger.info(f"Installing prerequisites on {name}...")
                    
                    for j, cmd in enumerate(prereq_cmds):
                        logger.info(f"  Prereq [{j+1}/{len(prereq_cmds)}]: {cmd[:50]}...")
                        exit_status, output, error = ssh_execute_with_retry(ssh, cmd)
                        if exit_status != 0:
                            logger.warning(f"Prereq command failed on {name}: {cmd}. Error: {error}")

                    # Join node to cluster
                    role = 'edge' if node_type == 'edge' else 'iot'
                    logger.info(f"Joining {name} as {role} node...")
                    result = ssh_join_node_generic(ip, username, password, MASTER_IP, token, name, role)
                    
                    if not result["success"]:
                        logger.error(f"Failed to join {name}: {result['error']}")
                        # Continue with other nodes even if one fails
                        continue

                    ssh.close()
                    await progress_manager.send_progress({
                        "type": "progress",
                        "percent": progress + 2,
                        "message": f"Successfully joined {name} to cluster"
                    })
                    logger.info(f"Successfully joined {name} to cluster")

                except Exception as e:
                    logger.error(f"Failed to setup node {name}: {str(e)}")
                    # Continue with other nodes

        # ========== UPDATED SECTION: ConfigMap Creation and Manifest Application ==========
        
        # Step 4: Create ConfigMap first
        await progress_manager.send_progress({
            "type": "progress",
            "percent": 95,
            "message": "Creating application ConfigMap...",
            "active_step": "step-apps"
        })

        # First, create the myapp-config ConfigMap
        detect_py_path = os.path.join(FILES_DIR, 'detect.py')
        if os.path.exists(detect_py_path):
            logger.info("Creating myapp-config ConfigMap...")
            result = subprocess.run([
                "kubectl", "create", "configmap", "myapp-config",
                "--from-file", f"detect.py={detect_py_path}",
                "--dry-run=client", "-o", "yaml"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Apply the ConfigMap
                apply_result = subprocess.run([
                    "kubectl", "apply", "-f", "-"
                ], input=result.stdout, capture_output=True, text=True)
                
                if apply_result.returncode == 0:
                    await progress_manager.send_progress({
                        "type": "progress",
                        "percent": 96,
                        "message": "Successfully created myapp-config ConfigMap"
                    })
                    logger.info("Successfully created myapp-config ConfigMap")
                else:
                    logger.error(f"Failed to apply ConfigMap: {apply_result.stderr}")
            else:
                logger.error(f"Failed to generate ConfigMap: {result.stderr}")
        else:
            logger.error(f"detect.py not found at {detect_py_path}")

        # Step 5: Apply other manifests
        await progress_manager.send_progress({
            "type": "progress",
            "percent": 97,
            "message": "Applying Kubernetes manifests..."
        })

        yaml_files = ['mediamtx-daemonset.yaml', 'myapp.yaml', 'configmap-mediamtx-endpoints.yaml', 'offloading-manager-pod.yaml']

        for i, yaml_file in enumerate(yaml_files):
            progress = 97 + int((i / len(yaml_files)) * 2)
            await progress_manager.send_progress({
                "type": "progress",
                "percent": progress,
                "message": f"Applying {yaml_file}..."
            })
            path = os.path.join(FILES_DIR, yaml_file)
            if os.path.exists(path):
                logger.info(f"Applying {yaml_file}...")
                
                # Special handling for myapp.yaml to ensure clean deployment
                if yaml_file == 'myapp.yaml':
                    # Delete existing StatefulSet to ensure fresh deployment with new image
                    delete_result = subprocess.run([
                        "kubectl", "delete", "statefulset", "myapp", "--ignore-not-found=true"
                    ], capture_output=True, text=True)
                    if delete_result.returncode == 0:
                        logger.info("Deleted existing myapp StatefulSet for fresh deployment")
                    time.sleep(2)  # Brief pause
                
                result = subprocess.run(["kubectl", "apply", "-f", path], capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"Failed to apply {yaml_file}: {result.stderr}")
                else:
                    await progress_manager.send_progress({
                        "type": "progress",
                        "percent": progress + 1,
                        "message": f"Successfully applied {yaml_file}"
                    })
                    logger.info(f"Successfully applied {yaml_file}")
            else:
                logger.warning(f"YAML file {yaml_file} not found")

        # ========== END UPDATED SECTION ==========

        # Step 6: Final checks
        await progress_manager.send_progress({
            "type": "progress",
            "percent": 99,
            "message": "Performing final checks...",
            "active_step": "step-complete"
        })
        logger.info("Deployment completed. Performing final checks...")
        
        try:
            # Check nodes
            nodes = v1.list_node()
            node_count = len(nodes.items) if hasattr(nodes, 'items') else 0
            
            # Get current worker nodes from database
            conn = sqlite3.connect('nodes.db')
            c = conn.cursor()
            c.execute("SELECT name FROM nodes WHERE name != ?", (MASTER_NAME,))
            worker_nodes = [row[0] for row in c.fetchall()]
            conn.close()
            
            worker_nodes_joined = len([n for n in worker_nodes if n in existing_nodes + [node[0] for node in nodes_to_join]])
            
            await progress_manager.send_progress({
                "type": "progress",
                "percent": 99,
                "message": f"Cluster now has {node_count} nodes",
                "active_step": "step-complete"
            })
            logger.info(f"Cluster now has {node_count} nodes")

            # Check pods
            pods = v1.list_namespaced_pod(namespace="default")
            running_pods = [p for p in pods.items if p.status.phase == "Running"] if hasattr(pods, 'items') else []
            
            # FIXED: Add active_step to completion message
            await progress_manager.send_progress({
                "type": "progress",
                "percent": 100,
                "message": f"Deployment completed successfully! Cluster has {node_count} nodes and {len(running_pods)} running pods",
                "completed": True,
                "active_step": "step-complete",
                "details": {
                    "master_setup": "completed",
                    "worker_nodes_joined": worker_nodes_joined,
                    "new_nodes_added": len(nodes_to_join),
                    "manifests_applied": len([f for f in yaml_files if os.path.exists(os.path.join(FILES_DIR, f))]),
                    "configmaps_created": 1
                }
            })
            logger.info(f"Found {len(running_pods)} running pods in default namespace")

        except Exception as e:
            logger.warning(f"Final checks incomplete: {e}")
            # FIXED: Add active_step to error completion too
            await progress_manager.send_progress({
                "type": "progress",
                "percent": 100,
                "message": f"Deployment completed (checks had issues: {str(e)})",
                "completed": True,
                "active_step": "step-complete"
            })

        return {
            "message": f"Deployment to all nodes completed successfully! Check Grafana dashboard at http://{MASTER_IP}:32000",
            "success": True,
            "details": {
                "master_setup": "completed",
                "worker_nodes_joined": worker_nodes_joined,
                "new_nodes_added": len(nodes_to_join),
                "manifests_applied": len([f for f in yaml_files if os.path.exists(os.path.join(FILES_DIR, f))]),
                "configmaps_created": 1
            }
        }

    except HTTPException:
        await progress_manager.send_progress({
            "type": "error",
            "message": "Deployment failed due to HTTP exception",
            "percent": 0
        })
        raise
    except Exception as e:
        await progress_manager.send_progress({
            "type": "error",
            "message": f"Deployment failed: {str(e)}",
            "percent": 0
        })
        logger.error(f"Deployment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")

# Handle OPTIONS requests for all endpoints
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    return JSONResponse(status_code=200, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
    })

@app.post("/api/refresh-token", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_active_user)):
    """Refresh JWT token without requiring re-login"""
    access_token_expires = timedelta(minutes=float(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    access_token = create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Helper functions
def get_master_node():
    """Get master node from database"""
    conn = sqlite3.connect('nodes.db')
    c = conn.cursor()
    c.execute("SELECT name, ip, username, password FROM nodes WHERE is_master = 1")
    master = c.fetchone()
    conn.close()
    
    if master:
        return {
            "name": master[0],
            "ip": master[1], 
            "username": master[2],
            "password": master[3]
        }
    return None

def validate_deployment_files():
    """Check if all required files exist"""
    missing_files = []
    for file in FILES_TO_COPY:
        file_path = os.path.join(FILES_DIR, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        raise HTTPException(
            status_code=500,
            detail=f"Missing required files: {', '.join(missing_files)}. Please add them to {FILES_DIR}"
        )
    
    logger.info("All deployment files are present")
    return True

def generate_node_provisioning_script(node_name: str, node_type: str, ssh_username: str, ssh_password: str) -> str:
    master_ip = os.getenv("MASTER_NODE_IP")
    token = os.getenv("K3S_TOKEN")
    
    return f"""#!/bin/bash
# Node provisioning script for {node_name} ({node_type})

# Install dependencies
sudo apt-get update
sudo apt-get install -y curl

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Kubernetes (k3s)
curl -sfL https://get.k3s.io | \\
K3S_TOKEN="{token}" \\
K3S_URL="https://{master_ip}:6443" \\
K3S_NODE_NAME="{node_name}" \\
INSTALL_K3S_EXEC="agent --node-label role={node_type} --node-label name={node_name}" \\
sh -

echo "Node {node_name} provisioned successfully"
"""

def apply_yaml(yaml_content: str, resource_type: str):
    try:
        # Write YAML to temporary file
        with open(f"/tmp/{resource_type}.yaml", "w") as f:
            f.write(yaml_content)

        # Apply using kubectl
        result = subprocess.run(
            ["kubectl", "apply", "-f", f"/tmp/{resource_type}.yaml"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(f"Failed to apply {resource_type}: {result.stderr}")

        return result.stdout
    except Exception as e:
        logger.error(f"Error applying YAML: {e}")
        raise

def get_master_node():
    """Get master node from database"""
    conn = sqlite3.connect('nodes.db')
    c = conn.cursor()
    c.execute("SELECT name, ip, username, password FROM nodes WHERE is_master = 1")
    master = c.fetchone()
    conn.close()
    
    if master:
        return {
            "name": master[0],
            "ip": master[1], 
            "username": master[2],
            "password": master[3]
        }
    return None

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8080))  # fallback to 8080 if not set
    uvicorn.run(app, host="0.0.0.0", port=port)
