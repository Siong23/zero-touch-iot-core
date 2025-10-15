1. Project Structure:
```bash
5G-ZSM-UI/
├── frontend/
│   ├── index.html
│   ├── script.js
├── backend/
│   ├── main.py
│   ├── nodes.db
│   ├── files
│   ├── requirements.txt
│   ├── grafana-values.yaml
│   ├── venv
│   ├── .env
│   ├── nodes.db
│   ├── config/
│   ├── models/
│   ├── routes/
|        ├──nodes.py
│   ├── utils/
│   ├── __pycache__
│   └── scripts/
```

2. Step 1: Create project directory:
```bash
mkdir -p ~/ZSM-UI/backend
cd ~/ZSM-UI/backend

sudo apt update
sudo apt install python3.10-venv
```

3. Step 2: Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

4. Step 3: Install required packages:
```bash
pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt] 
pip install python-dotenv requests kubernetes prometheus-client
pip install paramiko bcrypt
```

5.Step 4: Create directory structure:
```bash
mkdir -p config models routes utils scripts
```

6. Step 5: create file (content may see in Backend:
```bash
nano .env
nano requirements.txt
nano main.py
sudo nano /etc/systemd/system/ZSM-backend.service
```

7. Step 6: start and check status for backend service
```bash
sudo systemctl daemon-reload
sudo systemctl enable ZSM-backend
sudo systemctl start ZSM-backend
sudo systemctl status ZSM-backend

##restart
sudo systemctl daemon-reload
sudo systemctl restart ZSM-backend
sudo systemctl status ZSM-backend
```
