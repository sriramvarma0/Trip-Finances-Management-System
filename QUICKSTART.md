# QUICK START

Choose your platform:

## 🤖 Android (Termux)

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/sriramvarma0/Trip-Finances-Management-System/main/termux-deploy.sh)"
```

Or manually:
```bash
pkg update && pkg upgrade -y
pkg install -y python pip git
git clone https://github.com/sriramvarma0/Trip-Finances-Management-System.git
cd Trip-Finances-Management-System
pip install flask flask-cors
python app.py
```

**Then open:** `http://localhost:8000` on your phone

---

## 🐧 Linux / macOS

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/sriramvarma0/Trip-Finances-Management-System/main/linux-deploy.sh)"
```

Or manually:
```bash
git clone https://github.com/sriramvarma0/Trip-Finances-Management-System.git
cd Trip-Finances-Management-System
python3 -m venv venv
source venv/bin/activate  # On macOS
pip install -r requirements.txt
python app.py
```

**Then open:** `http://localhost:8000`

---

## 🪟 Windows

1. Download `windows-deploy.bat`
2. Double-click it
3. Follow the prompts
4. **Then open:** `http://localhost:8000`

Or manually:
```cmd
git clone https://github.com/sriramvarma0/Trip-Finances-Management-System.git
cd Trip-Finances-Management-System
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python app.py
```

---

## ☁️ Cloud (GCP, AWS, DigitalOcean)

See `README.md` for full Nginx + systemd setup.

Quick version:
```bash
apt update && apt install -y python3-pip git nginx
pip3 install flask flask-cors
git clone https://github.com/sriramvarma0/Trip-Finances-Management-System.git /opt/tripapp
cd /opt/tripapp
sudo cp tripapp.service /etc/systemd/system/
sudo systemctl start tripapp
```

---

## ✅ What Happens

1. ✓ Installs Python and dependencies
2. ✓ Clones the repository
3. ✓ Runs the app on `http://localhost:8000`
4. ✓ Creates SQLite database automatically

---

## 📖 Full Documentation

See `README.md` for:
- Detailed setup for each platform
- Background/persistent app setup
- Deployment troubleshooting
- API documentation
- Architecture overview
