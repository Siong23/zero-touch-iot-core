1. index.html:
```bash
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edge Computing Management</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary-color: #2c3e50;
            --secondary-color: #3498db;
            --accent-color: #e74c3c;
            --light-bg: #f8f9fa;
        }

        body {
            background-color: var(--light-bg);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            min-height: 100vh;
        }

        /* Sidebar Styles */
        #sidebar {
            width: 250px;
            background: var(--primary-color);
            color: white;
            transition: all 0.3s;
            position: fixed;
            height: 100vh;
            overflow-y: auto;
            z-index: 1000;
        }

        #sidebar .sidebar-header {
            padding: 20px;
            background: rgba(0, 0, 0, 0.2);
            text-align: center;
        }

        #sidebar .user-info {
            padding: 15px 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        #sidebar ul.components {
            padding: 20px 0;
        }

        #sidebar ul li a {
            padding: 15px 30px;
            display: block;
            color: rgba(255, 255, 255, 0.9);
            text-decoration: none;
            transition: all 0.3s;
        }

        #sidebar ul li a:hover {
            color: #fff;
            background: rgba(255, 255, 255, 0.1);
        }

        #sidebar ul li a.active {
            background: var(--secondary-color);
            color: white;
        }

        #sidebar ul li a i {
            margin-right: 10px;
        }

        /* Content Styles */
        #content {
            width: calc(100% - 250px);
            margin-left: 250px;
            padding: 20px;
            transition: all 0.3s;
        }

        .dashboard-card {
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }

        .card-header {
            background: var(--primary-color);
            color: white;
            padding: 15px 20px;
            border-radius: 10px 10px 0 0 !important;
            font-weight: 600;
        }

        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 5px;
        }

        .status-online {
            background-color: #28a745;
        }

        .status-offline {
            background-color: #dc3545;
        }

        .status-warning {
            background-color: #ffc107;
        }

        .deploy-btn {
            background: linear-gradient(45deg, #3498db, #2c3e50);
            border: none;
            padding: 12px 25px;
            font-weight: 600;
            color: white;
        }

        .stats-box {
            text-align: center;
            padding: 20px;
            border-radius: 8px;
            background: white;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
        }

        .stats-number {
            font-size: 24px;
            font-weight: 700;
            color: var(--secondary-color);
        }

        .table thead th {
            background: var(--primary-color);
            color: white;
        }

        .action-btn {
            padding: 5px 10px;
            margin: 0 3px;
            border-radius: 4px;
            font-size: 14px;
        }

        .page-section {
            display: none;
        }

        .page-section.active {
            display: block;
        }

        .grafana-dashboard {
            width: 100%;
            height: 600px;
            border: none;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .logout-btn {
            position: absolute;
            top: 20px;
            right: 20px;
        }

        .form-check-input:checked {
            background-color: #ffc107;
            border-color: #ffc107;
        }

        .form-check-label {
            font-weight: 500;
        }

        /* Loading spinner */
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, .3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to {
                transform: rotate(360deg);
            }
        }

        /* Mobile Responsiveness */
        @media (max-width: 768px) {
            #sidebar {
                margin-left: -250px;
                position: fixed;
            }

            #sidebar.active {
                margin-left: 0;
            }

            #content {
                width: 100%;
                margin-left: 0;
            }

            #sidebarCollapse {
                display: block;
            }

            .logout-btn {
                position: relative;
                top: 0;
                right: 0;
                margin-bottom: 15px;
            }
        }
    </style>
</head>

<!-- Login Modal -->
<div class="modal fade" id="loginModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header bg-primary text-white">
                <h5 class="modal-title">Login</h5>
            </div>
            <div class="modal-body">
                <form id="login-form">
                    <div class="mb-3">
                        <label class="form-label">Username</label>
                        <input type="text" class="form-control" id="username" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Password</label>
                        <input type="password" class="form-control" id="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Login</button>
                </form>
            </div>
        </div>
    </div>
</div>

<body>
    <!-- Sidebar -->
    <nav id="sidebar">
        <div class="sidebar-header">
            <h4>ZSM Manager</h4>
        </div>

        <div class="user-info">
            <div class="d-flex align-items-center">
                <div class="rounded-circle bg-secondary d-flex align-items-center justify-content-center"
                    style="width: 40px; height: 40px;">
                    <i class="fas fa-user text-white"></i>
                </div>
                <div class="ms-3">
                    <div class="fw-bold">Admin User</div>
                    <small class="text-white-50">Administrator</small>
                </div>
            </div>
        </div>

        <ul class="list-unstyled components">
            <li>
                <a href="#dashboard" class="nav-link active" data-section="dashboard">
                    <i class="fas fa-tachometer-alt"></i> Dashboard
                </a>
            </li>
            <li>
                <a href="#user-management" class="nav-link" data-section="user-management">
                    <i class="fas fa-users"></i> User Management
                </a>
            </li>
            <li>
                <a href="#edge-nodes" class="nav-link" data-section="edge-nodes">
                    <i class="fas fa-desktop"></i> Edge Nodes
                </a>
            </li>
            <li>
                <a href="#iot-nodes" class="nav-link" data-section="iot-nodes">
                    <i class="fas fa-microchip"></i> IoT Nodes
                </a>
            </li>
        </ul>
    </nav>

    <!-- Content -->
    <div id="content">
        <!-- Header -->
        <div class="d-flex justify-content-between align-items-center mb-4">
            <button id="sidebarCollapse" class="btn btn-primary d-md-none">
                <i class="fas fa-bars"></i>
            </button>
            <h2 class="mb-0" id="page-title">Edge Computing Dashboard</h2>
            <button class="btn btn-outline-danger logout-btn">
                <i class="fas fa-sign-out-alt me-1"></i> Logout
            </button>
        </div>

        <!-- Dashboard Section -->
        <section id="dashboard" class="page-section active">
            <!-- Stats Overview -->
            <div class="row mb-4">
                <div class="col-md-3 col-sm-6 mb-3">
                    <div class="stats-box">
                        <div class="stats-number" id="total-nodes">0</div>
                        <div class="stats-label">Total Nodes</div>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6 mb-3">
                    <div class="stats-box">
                        <div class="stats-number" id="edge-nodes-count">0</div>
                        <div class="stats-label">Edge Nodes</div>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6 mb-3">
                    <div class="stats-box">
                        <div class="stats-number" id="iot-nodes-count">0</div>
                        <div class="stats-label">IoT Nodes</div>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6 mb-3">
                    <div class="stats-box">
                        <div class="stats-number" id="avg-cpu">0%</div>
                        <div class="stats-label">Avg CPU Usage</div>
                    </div>
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="d-flex flex-wrap gap-3">
                        <button class="btn deploy-btn" id="deploy-all-btn">
                            <i class="fas fa-rocket me-2"></i> Deploy to All Nodes
                        </button>
                    </div>
                </div>
            </div>

            <!-- Grafana Dashboard Embed -->
            <div class="dashboard-card">
                <div class="card-header">
                    <i class="fas fa-chart-bar me-2"></i> Grafana Dashboard
                </div>
                <div class="card-body">
                    <iframe
                        src="http://192.168.0.147:32000/d/7d57716318ee0dddbac5a7f451fb7753/node-exporter-nodes?orgId=1&from=now-1h&to=now&timezone=utc&var-datasource=prometheus&var-cluster=&var-instance=192.168.0.124:9100&refresh=30s&kiosk"
                        width="100%" height="800" frameborder="0">
                    </iframe>
                    <div class="text-center mt-3">
                        <small class="text-muted">If the dashboard doesn't load, or want see more detail information, <a
                                href="http://192.168.0.147:32000" target="_blank">click here to open it in a new
                                tab</a></small>
                    </div>
                </div>
            </div>
        </section>

        <!-- User Management Section -->
        <section id="user-management" class="page-section">
            <div class="dashboard-card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <span><i class="fas fa-users me-2"></i> User Management</span>
                    <button class="btn btn-sm btn-light">
                        <i class="fas fa-plus me-1"></i> Add User
                    </button>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Username</th>
                                    <th>Email</th>
                                    <th>Role</th>
                                    <th>Status</th>
                                    <th>Last Login</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <!-- User data will be populated dynamically -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </section>

        <!-- Edge Nodes Section -->
        <section id="edge-nodes" class="page-section">
            <div class="dashboard-card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <span><i class="fas fa-desktop me-2"></i> Edge Nodes</span>
                    <button id="add-edge-btn" class="btn btn-sm btn-success">
                        <i class="fas fa-plus me-1"></i> Add Edge Node
                    </button>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>IP Address</th>
                                    <th>Status</th>
                                    <th>CPU Utilisation</th>
                                    <th>Memory</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <!-- Edge nodes data will be populated dynamically from API -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </section>

        <!-- Add Edge Node Modal -->
        <div class="modal fade" id="addEdgeNodeModal" tabindex="-1" aria-labelledby="addEdgeNodeModalLabel"
            aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="addEdgeNodeModalLabel">Add Edge Node</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <form id="addEdgeNodeForm">
                            <div class="mb-3">
                                <label for="edgeNodeName" class="form-label">Node Name</label>
                                <input type="text" class="form-control" id="edgeNodeName" required
                                    placeholder="e.g., nuc3, lim-3021">
                            </div>
                            <div class="mb-3">
                                <label for="edgeNodeIP" class="form-label">IP Address</label>
                                <input type="text" class="form-control" id="edgeNodeIP" required
                                    placeholder="e.g., 192.168.0.101">
                            </div>
                            <div class="mb-3">
                                <label for="edgeSshUsername" class="form-label">SSH Username</label>
                                <input type="text" class="form-control" id="edgeSshUsername" required
                                    placeholder="e.g., ubuntu, admin">
                            </div>
                            <div class="mb-3">
                                <label for="edgeSshPassword" class="form-label">SSH Password</label>
                                <input type="password" class="form-control" id="edgeSshPassword" required
                                    placeholder="SSH password for the device">
                            </div>
                            <!-- ADD THIS NEW SECTION -->
                            <div class="mb-3 form-check">
                                <input type="checkbox" class="form-check-input" id="edgeIsMaster">
                                <label class="form-check-label" for="edgeIsMaster">
                                    <i class="fas fa-crown text-warning me-1"></i> Set as Master Node
                                </label>
                            </div>
                            <div class="alert alert-info">
                                <small><i class="fas fa-info-circle me-1"></i> Master node will run Kubernetes control
                                    plane and manage the cluster</small>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-primary" form="addEdgeNodeForm">Add Node</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- IoT Nodes Section -->
        <section id="iot-nodes" class="page-section">
            <div class="dashboard-card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <span><i class="fas fa-microchip me-2"></i> IoT Nodes </span>
                    <button id="add-iot-btn" class="btn btn-sm btn-success">
                        <i class="fas fa-plus"></i> Add IoT Node
                    </button>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>IP Address</th>
                                    <th>Status</th>
                                    <th>CPU Utilisation</th>
                                    <th>Memory</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="iotNodesTableBody">
                                <!-- IoT nodes data will be populated dynamically from API -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </section>

        <!-- Add IoT Node Modal -->
        <div class="modal fade" id="addNodeModal" tabindex="-1" aria-labelledby="addNodeModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="addNodeModalLabel">Add IoT Node</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <form id="addNodeForm">
                            <div class="mb-3">
                                <label for="nodeName" class="form-label">Node Name</label>
                                <input type="text" class="form-control" id="nodeName" required
                                    placeholder="e.g., rpi2, iot-device-1">
                            </div>
                            <div class="mb-3">
                                <label for="nodeIP" class="form-label">IP Address</label>
                                <input type="text" class="form-control" id="nodeIP" required
                                    placeholder="e.g., 192.168.0.100">
                            </div>
                            <div class="mb-3">
                                <label for="sshUsername" class="form-label">SSH Username</label>
                                <input type="text" class="form-control" id="sshUsername" required
                                    placeholder="e.g., pi, ubuntu" value="pi">
                            </div>
                            <div class="mb-3">
                                <label for="sshPassword" class="form-label">SSH Password</label>
                                <input type="password" class="form-control" id="sshPassword" required
                                    placeholder="SSH password for the device" value="raspberry">
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-primary" form="addNodeForm">Add Node</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Session Warning Container -->
        <div id="session-warning" class="position-fixed top-0 end-0 m-3" style="z-index: 9999; width: 350px;"></div>

        <!-- Bootstrap & jQuery -->
        <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>


        <!-- JavaScript file -->
        <script src="script.js"></script>

</body>

</html>
```


2. script.js:
```bash
// script.js
$(document).ready(function () {
    const API_BASE_URL = 'http://192.168.0.147:8080';
    const API_BASE = `${API_BASE_URL}/api`;
    let edgeNodesData = [];
    let iotNodesData = [];
    let refreshInterval = 30000; // 30 seconds
    let refreshTimer = null;
    let sessionWarningTimer = null;
    let tokenRefreshTimer = null;

    // =========================
    // WEBSOCKET PROGRESS MANAGER
    // =========================
    let progressWebSocket = null;
    let deploymentInProgress = false;

    function connectProgressWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `ws://192.168.0.147:8080/ws/progress`;

        console.log('Connecting to WebSocket:', wsUrl);

        progressWebSocket = new WebSocket(wsUrl);

        progressWebSocket.onopen = function () {
            console.log('✅ Progress WebSocket connected');
            addLog('🔌 Connected to progress tracker');
        };

        progressWebSocket.onmessage = function (event) {
            console.log('📨 WebSocket message received:', event.data);
            try {
                const data = JSON.parse(event.data);
                handleProgressUpdate(data);
            } catch (error) {
                console.error('❌ Failed to parse WebSocket message:', error);
            }
        };

        progressWebSocket.onclose = function (event) {
            console.log('🔌 Progress WebSocket disconnected:', event.code, event.reason);
            addLog('🔌 Progress connection lost');

            // Reconnect after 3 seconds if deployment is in progress
            if (deploymentInProgress) {
                console.log('🔄 Reconnecting WebSocket...');
                setTimeout(connectProgressWebSocket, 3000);
            }
        };

        progressWebSocket.onerror = function (error) {
            console.error('❌ WebSocket error:', error);
            addLog('❌ Progress connection error');
        };
    }

    function handleProgressUpdate(data) {
        console.log('Progress update:', data);

        switch (data.type) {
            case 'progress':
                updateProgress(data.percent, data.message);

                // Update active step if provided
                if (data.active_step) {
                    // Reset all steps to default first
                    ['step-master', 'step-workers', 'step-apps', 'step-complete'].forEach(step => {
                        updateStep(step, 'default');
                    });
                    // Activate the current step
                    updateStep(data.active_step, 'active');
                    // Mark previous steps as completed
                    const steps = ['step-master', 'step-workers', 'step-apps', 'step-complete'];
                    const currentIndex = steps.indexOf(data.active_step);
                    for (let i = 0; i < currentIndex; i++) {
                        updateStep(steps[i], 'completed');
                    }
                }

                // Handle completion - FIXED
                if (data.completed === true) {
                    console.log('✅ Deployment completed!');
                    deploymentInProgress = false;

                    // Show success message
                    updateProgress(100, 'Deployment completed successfully!');
                    updateStep('step-complete', 'completed');

                    // Show close button
                    $('#closeDeployModalBtn').show();
                    $('#closeDeployModal').show();

                    // Add completion details to log
                    if (data.details) {
                        addLog('📊 Master setup: ' + data.details.master_setup);
                        addLog('📊 Worker nodes joined: ' + data.details.worker_nodes_joined);
                        addLog('📊 New nodes added: ' + data.details.new_nodes_added);
                        addLog('📊 Manifests applied: ' + data.details.manifests_applied);
                    }

                    // Refresh data after deployment
                    setTimeout(() => {
                        loadDashboardStats();
                        loadEdgeNodes();
                        loadIoTNodes();
                    }, 2000);
                }
                break;

            case 'error':
                console.error('❌ Deployment error:', data.message);
                updateProgress(0, 'Deployment failed: ' + data.message);
                deploymentInProgress = false;

                // Mark all steps as failed
                ['step-master', 'step-workers', 'step-apps', 'step-complete'].forEach(step => {
                    updateStep(step, 'failed');
                });

                // Show close button
                $('#closeDeployModalBtn').show();
                $('#closeDeployModal').show();
                break;
        }
    }

    // Initialize WebSocket when page loads
    connectProgressWebSocket();

    // =========================
    // Authentication
    // =========================

    // Show login modal if no token
    if (!localStorage.getItem("token")) {
        $('#loginModal').modal('show');
    }

    // Handle login form
    $('#login-form').submit(function (e) {
        e.preventDefault();
        const username = $('#username').val();
        const password = $('#password').val();

        $.ajax({
            url: `${API_BASE_URL}/token`,
            method: "POST",
            data: { username, password },
            success: function (res) {
                localStorage.setItem("token", res.access_token);
                $('#loginModal').modal('hide');

                // Start session management
                startTokenRefresh();
                startSessionWarning();

                loadDashboardStats();
                startAutoRefresh();

                // Load IoT nodes if needed
                loadIoTNodes();
            },
            error: function () {
                alert("Login failed. Please check your credentials.");
            }
        });
    });

    // Logout button
    $('.logout-btn').click(function () {
        if (confirm('Are you sure you want to logout?')) {
            // Clear all timers
            if (tokenRefreshTimer) clearInterval(tokenRefreshTimer);
            if (sessionWarningTimer) clearTimeout(sessionWarningTimer);
            if (refreshTimer) clearInterval(refreshTimer);

            localStorage.removeItem("token");
            $('#session-warning').empty();
            $('#loginModal').modal('show');
        }
    });

    // =========================
    // Session Management
    // =========================

    // Token refresh function
    async function refreshToken() {
        try {
            const token = localStorage.getItem('token');
            if (!token) return false;

            const response = await fetch(`${API_BASE}/refresh-token`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('token', data.access_token);
                console.log('Token refreshed successfully');
                return true;
            }
            return false;
        } catch (error) {
            console.error('Token refresh failed:', error);
            return false;
        }
    }

    // Start automatic token refresh
    function startTokenRefresh() {
        if (tokenRefreshTimer) clearInterval(tokenRefreshTimer);

        // Refresh 5 minutes before expiration (25 minutes)
        tokenRefreshTimer = setInterval(async () => {
            const success = await refreshToken();
            if (!success) {
                console.log('Token refresh failed, will retry in 5 minutes');
            }
        }, 25 * 60 * 1000); // 25 minutes
    }

    // Show session warning
    function showSessionWarning() {
        const warningHtml = `
            <div class="alert alert-warning alert-dismissible fade show shadow" role="alert">
                <div class="d-flex align-items-center">
                    <i class="fas fa-clock me-2 fs-5"></i>
                    <div>
                        <strong>Session Expiring Soon</strong><br>
                        Your session will expire in 5 minutes.
                        <div class="mt-2">
                            <button class="btn btn-sm btn-outline-success me-2" onclick="extendSession()">
                                <i class="fas fa-sync me-1"></i> Extend Session
                            </button>
                            <button class="btn btn-sm btn-outline-secondary" onclick="dismissWarning()">
                                Dismiss
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        $('#session-warning').html(warningHtml);
    }

    // Dismiss warning
    function dismissWarning() {
        $('#session-warning').empty();
    }

    // Start session warning timer
    function startSessionWarning() {
        if (sessionWarningTimer) clearTimeout(sessionWarningTimer);

        // Show warning 25 minutes after login (5 minutes before expiry)
        sessionWarningTimer = setTimeout(() => {
            showSessionWarning();
        }, 25 * 60 * 1000); // 25 minutes
    }

    // =========================
    // Sidebar & Navigation
    // =========================
    $('#sidebarCollapse').on('click', function () {
        $('#sidebar').toggleClass('active');
    });

    $('.nav-link').on('click', function (e) {
        e.preventDefault();

        $('.nav-link').removeClass('active');
        $(this).addClass('active');

        $('.page-section').removeClass('active');
        const sectionId = $(this).data('section');
        $(`#${sectionId}`).addClass('active');

        const sectionTitle = $(this).text().trim();
        $('#page-title').text(sectionTitle);

        if (sectionId === 'edge-nodes') {
            loadEdgeNodes();
        } else if (sectionId === 'iot-nodes') {
            loadIoTNodes();
        } else if (sectionId === 'dashboard') {
            setTimeout(() => {
                window.dispatchEvent(new Event('resize'));
            }, 300);
        }
        window.scrollTo(0, 0);
    });

    // =========================
    // Auto Refresh Function
    // =========================
    function startAutoRefresh() {
        if (refreshTimer) clearInterval(refreshTimer);
        refreshTimer = setInterval(() => {
            const activeSection = $('.page-section.active').attr('id');
            if (activeSection === 'dashboard') {
                loadDashboardStats();
            } else if (activeSection === 'edge-nodes') {
                loadEdgeNodes();
            } else if (activeSection === 'iot-nodes') {
                loadIoTNodes();
            }
        }, refreshInterval);
    }

    // =========================
    // Dashboard Stats
    // =========================
    loadDashboardStats();

    function loadDashboardStats() {
        $('.stats-number').html('<div class="loading-spinner mx-auto" style="width: 20px; height: 20px;"></div>');

        const token = localStorage.getItem("token");
        if (!token) {
            $('.stats-number').text('Please login');
            $('#loginModal').modal('show');
            return;
        }

        $.ajax({
            url: `${API_BASE}/edge-nodes`,
            method: "GET",
            headers: { "Authorization": "Bearer " + token },
            success: function (edgeData) {
                edgeNodesData = edgeData;

                $.ajax({
                    url: `${API_BASE}/iot-nodes`,
                    method: "GET",
                    headers: { "Authorization": "Bearer " + token },
                    success: function (iotData) {
                        iotNodesData = iotData;

                        $('#total-nodes').text(edgeData.length + iotData.length);
                        $('#edge-nodes-count').text(edgeData.length);
                        $('#iot-nodes-count').text(iotData.length);

                        let totalCpu = 0;
                        let nodeCount = 0;

                        edgeData.forEach(node => {
                            totalCpu += parseFloat(node.cpu.replace('%', '')) || 0;
                            nodeCount++;
                        });

                        iotData.forEach(node => {
                            totalCpu += parseFloat(node.cpu.replace('%', '')) || 0;
                            nodeCount++;
                        });

                        const avgCpu = nodeCount > 0 ? (totalCpu / nodeCount).toFixed(1) : 0;
                        $('#avg-cpu').text(`${avgCpu}%`);
                    },
                    error: function (xhr, status, error) {
                        if (xhr.status === 401) {
                            handleUnauthorizedError();
                        } else {
                            $('.stats-number').text('Error');
                            console.error('Failed to load IoT nodes data:', error);
                        }
                    }
                });
            },
            error: function (xhr, status, error) {
                if (xhr.status === 401) {
                    handleUnauthorizedError();
                } else {
                    $('.stats-number').text('Error');
                    console.error('Failed to load edge nodes data:', error);
                }
            }
        });
    }

    // =========================
    // Edge Nodes
    // =========================
    function initEdgeNodesModal() {
        $('#add-edge-btn').on('click', function () {
            console.log('Add Edge Node button clicked');
            $('#addEdgeNodeModal').modal('show');
        });

        $('#addEdgeNodeForm').on('submit', function (e) {
            e.preventDefault();
            handleAddEdgeNode(e);
        });

        $('#addEdgeNodeModal').on('hidden.bs.modal', function () {
            $('#addEdgeNodeForm')[0].reset();
        });
    }

    // In script.js - around line 250
    async function handleAddEdgeNode(e) {
        e.preventDefault();
        console.log('Add Edge Node form submitted');

        const name = $('#edgeNodeName').val();
        const ip = $('#edgeNodeIP').val();
        const sshUsername = $('#edgeSshUsername').val();
        const sshPassword = $('#edgeSshPassword').val();
        const isMaster = $('#edgeIsMaster').is(':checked');  // ADD THIS LINE

        console.log('Edge Node form data:', { name, ip, sshUsername, isMaster }); // Updated log

        const token = localStorage.getItem("token");
        if (!token) {
            alert("Please login first.");
            $('#loginModal').modal('show');
            return;
        }

        const submitBtn = $('#addEdgeNodeForm').find('button[type="submit"]');
        const originalText = submitBtn.html();
        submitBtn.html('<i class="fas fa-spinner fa-spin me-2"></i> Adding...');
        submitBtn.prop('disabled', true);

        try {
            const response = await fetch(`${API_BASE}/edge-nodes/add`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    name: name,
                    ip: ip,
                    ssh_username: sshUsername,
                    ssh_password: sshPassword,
                    is_master: isMaster  // ADD THIS LINE
                })
            });

            const data = await response.json();

            if (response.ok) {
                let message = data.message || "Edge node added successfully!";
                if (isMaster) {
                    message += " (Set as Master Node)";
                }
                alert(message);
                $('#addEdgeNodeModal').modal('hide');
                loadEdgeNodes();
                loadDashboardStats();
            } else {
                throw new Error(data.detail || data.error || 'Failed to add edge node');
            }
        } catch (error) {
            console.error('Error adding edge node:', error);
            alert(`Error adding edge node: ${error.message}`);
        } finally {
            submitBtn.html(originalText);
            submitBtn.prop('disabled', false);
        }
    }

    function loadEdgeNodes() {
        const tbody = $('#edge-nodes table tbody');
        tbody.html('<tr><td colspan="6" class="text-center py-4"><div class="loading-spinner mx-auto"></div> Loading edge nodes...</td></tr>');

        const token = localStorage.getItem("token");
        if (!token) {
            tbody.html('<tr><td colspan="6" class="text-center py-4 text-danger">Please login first</td></tr>');
            $('#loginModal').modal('show');
            return;
        }

        $.ajax({
            url: `${API_BASE}/edge-nodes`,
            method: "GET",
            headers: { "Authorization": "Bearer " + token },
            success: function (data) {
                edgeNodesData = data;
                tbody.empty();

                if (data.length === 0) {
                    tbody.html('<tr><td colspan="6" class="text-center py-4">No edge nodes found</td></tr>');
                    return;
                }

                data.forEach(node => {
                    const statusClass = node.status === 'online' ? 'status-online' :
                        (node.status === 'warning' ? 'status-warning' : 'status-offline');

                    const isMasterNode = node.name.toLowerCase().includes('nuc2') ||
                        node.name.toLowerCase().includes('master') ||
                        node.name.toLowerCase().includes('control-plane');

                    const deleteButton = isMasterNode
                        ? '<button class="btn btn-sm btn-danger action-btn" disabled title="Cannot delete master node"><i class="fas fa-lock me-1"></i> Protected</button>'
                        : `<button class="btn btn-sm btn-danger action-btn delete-edge-btn" data-node="${node.name}">Delete</button>`;

                    tbody.append(`
                    <tr>
                        <td>${node.name}</td>
                        <td>${node.ip}</td>
                        <td><span class="status-indicator ${statusClass}"></span> ${node.status}</td>
                        <td>${node.cpu}</td>
                        <td>${node.memory}</td>
                        <td>
                            <button class="btn btn-sm btn-info action-btn">View</button>
                            ${deleteButton}
                        </td>
                    </tr>
                `);
                });
            },
            error: function (xhr, status, error) {
                if (xhr.status === 401) {
                    handleUnauthorizedError();
                } else {
                    tbody.html('<tr><td colspan="6" class="text-center py-4 text-danger">Failed to load edge nodes data</td></tr>');
                    console.error('Failed to load edge nodes:', error);
                }
            }
        });
    }

    // =========================
    // IoT Nodes
    // =========================
    function initIoTNodesModal() {
        $('#add-iot-btn').on('click', function () {
            console.log('Add IoT Node button clicked');
            $('#addNodeModal').modal('show');
        });

        $('#addNodeForm').on('submit', function (e) {
            e.preventDefault();
            handleAddNode(e);
        });

        $('#addNodeModal').on('hidden.bs.modal', function () {
            $('#addNodeForm')[0].reset();
        });
    }

    async function handleAddNode(e) {
        e.preventDefault();
        console.log('Add Node form submitted');

        const name = $('#nodeName').val();
        const ip = $('#nodeIP').val();
        const sshUsername = $('#sshUsername').val();
        const sshPassword = $('#sshPassword').val();

        console.log('Form data:', { name, ip, sshUsername });

        const token = localStorage.getItem("token");
        if (!token) {
            alert("Please login first.");
            $('#loginModal').modal('show');
            return;
        }

        const submitBtn = $('#addNodeForm').find('button[type="submit"]');
        const originalText = submitBtn.html();
        submitBtn.html('<i class="fas fa-spinner fa-spin me-2"></i> Adding...');
        submitBtn.prop('disabled', true);

        try {
            const response = await fetch(`${API_BASE}/nodes/add`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    name: name,
                    ip: ip,
                    ssh_username: sshUsername,
                    ssh_password: sshPassword
                })
            });

            const data = await response.json();

            if (response.ok) {
                alert(data.message || "Node added successfully!");
                $('#addNodeModal').modal('hide');
                loadIoTNodes();
                loadDashboardStats();
            } else {
                throw new Error(data.detail || data.error || 'Failed to add node');
            }
        } catch (error) {
            console.error('Error adding node:', error);
            alert(`Error adding node: ${error.message}`);
        } finally {
            submitBtn.html(originalText);
            submitBtn.prop('disabled', false);
        }
    }

    function loadIoTNodes() {
        const tbody = $('#iot-nodes table tbody');
        tbody.html('<tr><td colspan="6" class="text-center py-4"><div class="loading-spinner mx-auto"></div> Loading IoT nodes...</td></tr>');

        const token = localStorage.getItem("token");
        if (!token) {
            tbody.html('<tr><td colspan="6" class="text-center py-4 text-danger">Please login first</td></tr>');
            $('#loginModal').modal('show');
            return;
        }

        $.ajax({
            url: `${API_BASE}/iot-nodes`,
            method: "GET",
            headers: { "Authorization": "Bearer " + token },
            success: function (data) {
                tbody.empty();

                if (data.length === 0) {
                    tbody.html('<tr><td colspan="6" class="text-center py-4">No IoT nodes found</td></tr>');
                    return;
                }

                data.forEach(node => {
                    const statusClass = node.status === 'online' ? 'status-online' :
                        (node.status === 'warning' ? 'status-warning' : 'status-offline');

                    tbody.append(`
                    <tr>
                        <td>${node.name}</td>
                        <td>${node.ip || node.ip_address}</td>
                        <td><span class="status-indicator ${statusClass}"></span> ${node.status}</td>
                        <td>${node.cpu || '-'}</td>
                        <td>${node.memory || '-'}</td>
                        <td>
                            <button class="btn btn-sm btn-info action-btn">View</button>
                            <button class="btn btn-sm btn-danger action-btn delete-iot-btn" data-node="${node.name}">Delete</button>
                        </td>
                    </tr>
                `);
                });
            },
            error: function (xhr, status, error) {
                if (xhr.status === 401) {
                    handleUnauthorizedError();
                } else {
                    tbody.html('<tr><td colspan="6" class="text-center py-4 text-danger">Failed to load IoT nodes data</td></tr>');
                    console.error('Failed to load IoT nodes:', error);
                }
            }
        });
    }

    // =========================
    // Delete Node Functions
    // =========================
    $(document).on('click', '.delete-iot-btn', function () {
        const nodeName = $(this).data('node');
        if (!confirm(`Are you sure you want to delete IoT node ${nodeName}?`)) return;

        const token = localStorage.getItem("token");
        if (!token) {
            alert("Please login first.");
            $('#loginModal').modal('show');
            return;
        }

        fetch(`${API_BASE}/nodes/${nodeName}`, {
            method: "DELETE",
            headers: { "Authorization": "Bearer " + token }
        })
            .then(async res => {
                const data = await res.json();
                if (res.ok) {
                    alert(data.message || "IoT node deleted successfully");
                    loadIoTNodes();
                    loadDashboardStats();
                } else {
                    const errMsg = data.detail || data.message || JSON.stringify(data);
                    throw new Error(errMsg);
                }
            })
            .catch(err => {
                console.error("Delete error:", err);
                alert("Error deleting IoT node: " + err.message);
            });
    });

    $(document).on('click', '.delete-edge-btn', function () {
        const nodeName = $(this).data('node');
        if (!confirm(`Are you sure you want to delete Edge node ${nodeName}?`)) return;

        const token = localStorage.getItem("token");
        if (!token) {
            alert("Please login first.");
            $('#loginModal').modal('show');
            return;
        }

        fetch(`${API_BASE}/nodes/${nodeName}`, {
            method: "DELETE",
            headers: { "Authorization": "Bearer " + token }
        })
            .then(res => {
                if (res.ok) {
                    return res.json();
                } else {
                    return res.json().then(err => { throw new Error(err.detail || 'Delete failed'); });
                }
            })
            .then(data => {
                alert(data.message || "Edge node deleted successfully");
                loadEdgeNodes();
                loadDashboardStats();
            })
            .catch(err => {
                console.error(err);
                alert(`Error deleting edge node: ${err.message}`);
            });
    });

    // =========================
    // Deploy to All Nodes
    // =========================
    $('#deploy-all-btn').click(function () {
        if (confirm('Are you sure you want to deploy to all nodes? This will setup the complete cluster including master node, worker nodes, and all applications.')) {
            const token = localStorage.getItem("token");
            if (!token) {
                alert('Please login first');
                $('#loginModal').modal('show');
                return;
            }

            // Show deployment progress modal
            showDeploymentProgressModal();

            // Start deployment
            deployToAllNodes(token);
        }
    });

    function showDeploymentProgressModal() {
        const modalHtml = `
            <div class="modal fade" id="deployProgressModal" tabindex="-1" data-bs-backdrop="static">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title">
                                <i class="fas fa-rocket me-2"></i>Cluster Deployment Progress
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close" id="closeDeployModal" style="display: none;"></button>
                        </div>
                        <div class="modal-body">
                            <div class="progress mb-3" style="height: 25px;">
                                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                     role="progressbar" style="width: 0%" id="deployProgressBar">
                                    <span class="fw-bold">0%</span>
                                </div>
                            </div>
                            
                            <div class="deployment-steps">
                                <div class="step" id="step-master">
                                    <i class="fas fa-circle-notch fa-spin text-primary me-2"></i>
                                    <span>Setting up master node...</span>
                                </div>
                                <div class="step text-muted" id="step-workers">
                                    <i class="far fa-clock me-2"></i>
                                    <span>Setting up worker nodes...</span>
                                </div>
                                <div class="step text-muted" id="step-apps">
                                    <i class="far fa-clock me-2"></i>
                                    <span>Deploying applications...</span>
                                </div>
                                <div class="step text-muted" id="step-complete">
                                    <i class="far fa-clock me-2"></i>
                                    <span>Finalizing deployment...</span>
                                </div>
                            </div>
                            
                            <div class="log-container mt-3" style="max-height: 200px; overflow-y: auto; background: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 12px;">
                                <div id="deployLogs">Starting deployment...</div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" id="closeDeployModalBtn" style="display: none;">
                                <i class="fas fa-times me-1"></i> Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        $('#deployProgressModal').remove();
        $('body').append(modalHtml);

        const modal = new bootstrap.Modal(document.getElementById('deployProgressModal'));
        modal.show();

        // Add event listener for close button
        $('#closeDeployModalBtn').on('click', function () {
            modal.hide();
        });
    }

    // Progress tracking functions
    function updateProgress(percent, message) {
        $('#deployProgressBar').css('width', percent + '%').text(percent + '%');
        addLog('📢 ' + message)
    }

    function updateStep(stepId, status) {
        const step = $('#' + stepId);
        const icon = step.find('i');

        step.removeClass('text-muted active completed text-success text-danger');
        icon.removeClass('fa-circle-notch fa-spin far fa-check-circle fa-times-circle text-primary');

        switch (status) {
            case 'active':
                step.addClass('active');
                icon.addClass('fas fa-circle-notch fa-spin text-primary');
                break;
            case 'completed':
                step.addClass('completed text-success');
                icon.addClass('fas fa-check-circle text-success');
                break;
            case 'failed':
                step.addClass('text-danger');
                icon.addClass('fas fa-times-circle text-danger');
                break;
            default:
                step.addClass('text-muted');
                icon.addClass('far fa-clock');
        }
    }

    function addLog(message) {
        const timestamp = new Date().toLocaleTimeString();
        $('#deployLogs').prepend(`<div>[${timestamp}] ${message}</div>`);
        $('#deployLogs').scrollTop(0);
    }

    // =========================
    // Deploy to All Nodes with REAL Progress (WebSocket)
    // =========================
    async function deployToAllNodes(token) {
        const button = $('#deploy-all-btn');
        const originalText = button.html();
        button.html('<i class="fas fa-spinner fa-spin me-2"></i> Deploying...');
        button.prop('disabled', true);

        // Reset progress modal for new deployment
        deploymentInProgress = true;
        updateProgress(0, 'Starting deployment...');

        // Reset all steps to default
        ['step-master', 'step-workers', 'step-apps', 'step-complete'].forEach(step => {
            updateStep(step, 'default');
        });

        // Start with master step active
        updateStep('step-master', 'active');
        $('#closeDeployModalBtn').hide();
        $('#closeDeployModal').hide();
        $('#deployLogs').html('Starting deployment...');

        // Ensure WebSocket is connected
        if (!progressWebSocket || progressWebSocket.readyState !== WebSocket.OPEN) {
            console.log('Connecting WebSocket for progress tracking...');
            connectProgressWebSocket();
            // Wait a bit for WebSocket to connect
            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        try {
            const response = await fetch(`${API_BASE}/deploy/all`, {
                method: "POST",
                headers: {
                    "Authorization": "Bearer " + token,
                    "Content-Type": "application/json"
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Deployment failed with status: ' + response.status);
            }

            const data = await response.json();
            console.log('Deployment API response:', data);

            // Note: Progress updates come via WebSocket, so we don't update UI here
            // The WebSocket handler will handle all real-time updates

        } catch (error) {
            console.error('Deployment API error:', error);
            deploymentInProgress = false;

            // Update UI to show failure
            updateProgress(0, 'Deployment failed: ' + error.message);

            // Mark all steps as failed
            ['step-master', 'step-workers', 'step-apps', 'step-complete'].forEach(step => {
                updateStep(step, 'failed');
            });

            addLog('❌ Deployment failed: ' + error.message);

            // Show close button
            $('#closeDeployModalBtn').show();
            $('#closeDeployModal').show();
        } finally {
            button.html(originalText);
            button.prop('disabled', false);
        }
    }

    // =========================
    // Helper Functions
    // =========================
    function handleUnauthorizedError() {
        alert('Session expired. Please login again.');
        localStorage.removeItem("token");
        $('#loginModal').modal('show');

        $('.stats-number').text('Please login');
        $('#edge-nodes table tbody').html('<tr><td colspan="6" class="text-center py-4">Please login to view data</td></tr>');
        $('#iot-nodes table tbody').html('<tr><td colspan="6" class="text-center py-4">Please login to view data</td></tr>');
    }

    // Initialize modals
    initIoTNodesModal();
    initEdgeNodesModal();

    // Fix Grafana gauge layout on first load
    window.addEventListener("load", () => {
        window.dispatchEvent(new Event("resize"));
    });
});

// Global functions for session warnings
async function extendSession() {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
        const response = await fetch('http://192.168.0.147:8080/api/refresh-token', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('token', data.access_token);
            $('#session-warning').html(`
                <div class="alert alert-success alert-dismissible fade show shadow" role="alert">
                    <i class="fas fa-check-circle me-2"></i>
                    Session extended successfully!
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `);
            setTimeout(() => $('#session-warning').empty(), 3000);
        }
    } catch (error) {
        console.error('Session extension failed:', error);
    }
}

function dismissWarning() {
    $('#session-warning').empty();
}

// CSS for deployment progress
const style = document.createElement('style');
style.textContent = `
    .deployment-steps {
        border-left: 3px solid #e9ecef;
        padding-left: 15px;
        margin-left: 10px;
    }

    .step {
        padding: 8px 0;
        border-bottom: 1px solid #f8f9fa;
        transition: all 0.3s ease;
    }

    .step.active {
        font-weight: 600;
        color: #0d6efd;
        background: rgba(13, 110, 253, 0.1);
        padding: 8px 12px;
        border-radius: 5px;
        margin: 2px 0;
    }

    .step.completed {
        color: #198754 !important;
        background: rgba(25, 135, 84, 0.1);
        padding: 8px 12px;
        border-radius: 5px;
        margin: 2px 0;
    }

    .step.failed {
        color: #dc3545 !important;
        background: rgba(220, 53, 69, 0.1);
        padding: 8px 12px;
        border-radius: 5px;
        margin: 2px 0;
    }

    .log-container {
        background: #1e1e1e !important;
        color: #d4d4d4;
        font-family: 'Courier New', monospace;
        border: 1px solid #444;
    }

    .log-container div {
        padding: 2px 0;
        border-bottom: 1px solid #2d2d2d;
    }

    .hidden {
        display: none !important;
    }
    
    .modal {
        z-index: 1055;
    }
    
    .modal-backdrop {
        z-index: 1050;
    }
    
    #closeDeployModalBtn {
        transition: all 0.3s ease;
    }
`;
document.head.appendChild(style);
```
