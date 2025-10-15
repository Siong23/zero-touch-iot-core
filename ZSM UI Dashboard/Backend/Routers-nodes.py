# nodes.py
from fastapi import APIRouter, HTTPException, Depends
from kubernetes import client, config
import requests
import logging
import sqlite3
import os

router = APIRouter(prefix="/api")

# =========================
# Kubernetes Setup
# =========================
try:
    config.load_kube_config()
    print("Loaded local kubeconfig")
except:
    config.load_incluster_config()
    print("Loaded in-cluster config")

v1 = client.CoreV1Api()
logger = logging.getLogger(__name__)

PROMETHEUS_URL = "http://localhost:9090"

# =========================
# Database Setup
# =========================
DB_PATH = os.path.join(os.path.dirname(__file__), "../iot_nodes.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# =========================
# Helper Functions
# =========================
def get_cpu_usage_percent(node_name: str) -> str:
    """Fetch CPU usage percentage for a node from Prometheus."""
    try:
        query = f'100 - (avg by (instance) (rate(node_cpu_seconds_total{{mode="idle", instance=~"{node_name}.*"}}[5m])) * 100)'
        response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})
        result = response.json()

        if result["status"] == "success" and result["data"]["result"]:
            value = float(result["data"]["result"][0]["value"][1])
            return f"{round(value, 1)}%"
        else:
            return "0%"
    except Exception as e:
        logger.error(f"Error fetching CPU usage for {node_name}: {e}")
        return "0%"

def get_node_status(node_name: str):
    """Check if node exists in cluster and return (status, cpu, memory)."""
    try:
        nodes = v1.list_node().items
        for node in nodes:
            if node.metadata.name == node_name:
                status = "online" if node.status.conditions[-1].status == "True" else "offline"
                mem_capacity = node.status.capacity.get("memory", "0")
                cpu_usage = get_cpu_usage_percent(node_name)
                return status, cpu_usage, mem_capacity
        return "offline", "0%", "0"
    except Exception as e:
        logger.error(f"Error checking node status: {e}")
        return "offline", "0%", "0"

# =========================
# Edge Nodes
# =========================
@router.get("/edge-nodes")
def get_edge_nodes():
    nodes = v1.list_node().items
    edge_nodes = []

    for node in nodes:
        node_name = node.metadata.name
        if "nuc" in node_name or "lim" in node_name:  
            status = "online" if node.status.conditions[-1].status == "True" else "offline"
            mem_capacity = node.status.capacity.get("memory", "0")
            cpu_usage = get_cpu_usage_percent(node_name)

            edge_nodes.append({
                "name": node_name,
                "ip": node.status.addresses[0].address,
                "status": status,
                "cpu": cpu_usage,
                "memory": mem_capacity
            })
    return edge_nodes

# =========================
# IoT Nodes
# =========================
@router.get("/iot-nodes")
def get_iot_nodes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM nodes WHERE role = 'iot'")
    rows = cur.fetchall()
    conn.close()

    iot_nodes = []
    for row in rows:
        status, cpu, mem = get_node_status(row["name"])
        iot_nodes.append({
            "name": row["name"],
            "ip_address": row["ip_address"],
            "role": row["role"],
            "rtsp_url": row["rtsp_url"],
            "status": status,
            "cpu": cpu,
            "memory": mem
        })
    return iot_nodes
