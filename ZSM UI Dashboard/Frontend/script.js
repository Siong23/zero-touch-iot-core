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
