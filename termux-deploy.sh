#!/data/data/com.termux/files/usr/bin/bash
set -e

pkg update -y
pkg upgrade -y
pkg install -y python git

cd "$HOME"
if [ -d "Trip-Finances-Management-System/.git" ]; then
  cd Trip-Finances-Management-System
  git pull origin main
else
  git clone https://github.com/sriramvarma0/Trip-Finances-Management-System.git
  cd Trip-Finances-Management-System
fi

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "App running at http://127.0.0.1:8000"
python app.py
