## Setup on GCP VM (one time)

sudo apt update && sudo apt install python3-pip git nginx -y
pip3 install flask flask-cors
git clone <your-repo> /opt/tripapp
sudo cp /opt/tripapp/tripapp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tripapp
sudo systemctl start tripapp

## Nginx config (/etc/nginx/sites-available/tripapp)

server {
    listen 80;
    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}

sudo ln -s /etc/nginx/sites-available/tripapp /etc/nginx/sites-enabled/
sudo nginx -t && sudo nginx -s reload

## Deploy after every git push

ssh user@your-vm-ip
cd /opt/tripapp
git pull origin main
sudo systemctl restart tripapp

## Access
http://<your-vm-external-ip>
