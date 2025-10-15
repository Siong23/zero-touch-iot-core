1. Go to ZSM backend service:
```bash
sudo nano /etc/systemd/system/ZSM-backend.service
```

2. Copy and paste below content:
```bash
[Unit]
Description=ZSM Backend FastAPI Service
After=network.target

[Service]
# Run under your user
User=nuc2
Group=nuc2

# Set working directory to your backend project
WorkingDirectory=/home/nuc2/ZSM-UI/backend

# Load environment variables from .env
EnvironmentFile=/home/nuc2/ZSM-UI/backend/.env

# Start backend using Python entrypoint (main.py)
ExecStart=/home/nuc2/ZSM-UI/backend/venv/bin/python /home/nuc2/ZSM-UI/backend/main.py

# Restart policy
Restart=always
RestartSec=5
TimeoutStopSec=60

# Logging
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```
