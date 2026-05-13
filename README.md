# Trip Finances Management System

A lightweight expense tracking and settlement calculator for group trips, built with Flask and SQLite.

## Features

- Create and manage multiple trips
- Add expense transactions and person-to-person transfers
- Automatic balance calculation and settlement suggestions
- Itinerary management with timeline view
- Member management
- Edit mode for data control
- Works offline (localStorage + server sync)

---

## Deployment Options

### Option 1: Termux (Android)

Deploy directly on your Android phone using Termux.

#### Prerequisites
- Termux app installed on Android
- ~500MB free storage
- Internet connection

#### Quick Setup (Simple Copy-Paste)

Copy and paste these commands in Termux:

```bash
pkg update -y
pkg upgrade -y
pkg install -y python git
cd $HOME
git clone https://github.com/sriramvarma0/Trip-Finances-Management-System.git
cd Trip-Finances-Management-System
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```

If the repo is already cloned, use this instead:

```bash
cd $HOME/Trip-Finances-Management-System
git pull origin main
python -m pip install -r requirements.txt
python app.py
```

**Access the app:**
- Open browser on your phone (or another device on same network)
- Go to: `http://localhost:8000` (on phone) or `http://<your-phone-ip>:8000` (from another device)

**Find your phone IP:**
```bash
# In Termux:
ifconfig | grep "inet addr"
```

#### Keep App Running in Background (Termux)

1. Install and open **Termux:Boot** app from Play Store
2. Allow notifications for Termux
3. Create startup script:
   ```bash
   mkdir -p ~/.termux/boot
   cat > ~/.termux/boot/start-tripapp.sh << 'EOF'
   #!/bin/bash
   cd $HOME/Trip-Finances-Management-System
   python app.py
   EOF
   chmod +x ~/.termux/boot/start-tripapp.sh
   ```
4. Reboot device - app will auto-start

---

### Option 2: GCP VM (Cloud Deployment)

Deploy on Google Cloud Platform with Nginx and systemd.

#### One-Time Setup

```bash
# SSH into your GCP VM
ssh user@your-vm-ip

# Update and install dependencies
sudo apt update && sudo apt install python3-pip git nginx -y
pip3 install flask flask-cors

# Clone repository
git clone https://github.com/sriramvarma0/Trip-Finances-Management-System.git /opt/tripapp

# Copy systemd service file
sudo cp /opt/tripapp/tripapp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tripapp
sudo systemctl start tripapp
```

#### Nginx Configuration

Create/edit `/etc/nginx/sites-available/tripapp`:

```nginx
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/tripapp /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

#### Deploy After Updates

```bash
cd /opt/tripapp
git pull origin main
sudo systemctl restart tripapp
```

#### Access
- `http://<your-vm-external-ip>`

---

### Option 3: Local Development

```bash
# Clone repository
git clone https://github.com/sriramvarma0/Trip-Finances-Management-System.git
cd Trip-Finances-Management-System

# Install dependencies
pip install flask flask-cors

# Run development server
python app.py
```

Access at: `http://localhost:8000`

---

## Architecture

- **Backend:** Flask (Python) + SQLite
- **Frontend:** Vanilla JavaScript + CSS Grid
- **Database:** SQLite (data.db)
- **Static Files:** HTML/CSS/JS in `static/` folder

## API Endpoints

- `GET /api/trips` - List all trips
- `GET /api/trips/<trip_id>` - Get trip details
- `POST /api/trips` - Create new trip
- `GET /api/trips/<trip_id>/transactions` - List transactions
- `POST /api/trips/<trip_id>/transactions` - Add transaction
- `PUT /api/trips/<trip_id>/transactions/<tx_id>` - Update transaction
- `DELETE /api/trips/<trip_id>/transactions/<tx_id>` - Delete transaction
- `GET /api/trips/<trip_id>/settle` - Get settlement suggestions
- `GET /health` - Health check (production)

---

## File Structure

```
Trip-Finances-Management-System/
├── app.py                 # Flask backend
├── requirements.txt       # Python dependencies
├── data.db               # SQLite database (auto-created)
├── tripapp.service       # systemd service file (for Linux)
├── README.md             # This file
└── static/
    ├── index.html        # Main UI
    └── [CSS + JS embedded in HTML]
```

---

## Troubleshooting

### Termux Port Access
If you can't access from another device, check firewall:
- Most Android firewalls allow localhost:8000 access
- If blocked, whitelist Termux in your firewall settings

### Database Issues
If you see "database is locked" errors:
- Only one instance of app.py should run
- Close all other terminal windows running the app

### Port Already in Use
```bash
# Change port in app.py (line ~3700)
# Or kill existing process:
lsof -ti:8000 | xargs kill -9
```

---

## Security Notes

- Edit mode requires PIN (default: 1111, set via UI)
- No user authentication - for trusted groups only
- For production, use HTTPS with reverse proxy (Nginx + Let's Encrypt)
- Restrict CORS origins in `app.py` for production

---

## License

MIT

---

## Support

For issues, feature requests, or contributions:
https://github.com/sriramvarma0/Trip-Finances-Management-System
