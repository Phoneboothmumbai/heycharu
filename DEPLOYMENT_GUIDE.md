# Sales Brain - Vultr Ubuntu Server Deployment Guide

## Prerequisites
- Fresh Vultr Ubuntu 22.04 LTS server
- Domain name (optional but recommended)
- SSH access to the server

---

## Step 1: Initial Server Setup

```bash
# Connect to your server
ssh root@YOUR_SERVER_IP

# Update system packages
apt update && apt upgrade -y

# Set timezone
timedatectl set-timezone Asia/Kolkata

# Create a non-root user (recommended)
adduser heycharu
usermod -aG sudo heycharu

# Switch to new user
su - heycharu
```

---

## Step 2: Install Required Software

### Install Node.js 20.x
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version  # Should show v20.x
npm --version
```

### Install Python 3.11
```bash
sudo apt install -y python3.11 python3.11-venv python3-pip
python3.11 --version
```

### Install MongoDB
```bash
# Import MongoDB public GPG key
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Install MongoDB
sudo apt update
sudo apt install -y mongodb-org

# Start and enable MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
sudo systemctl status mongod
```

### Install Nginx
```bash
sudo apt install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Install Git
```bash
sudo apt install -y git
```

### Install PM2 (Process Manager)
```bash
sudo npm install -g pm2
```

### Install Yarn
```bash
sudo npm install -g yarn
```

---

## Step 3: Clone the Repository

```bash
cd /home/heycharu
git clone https://github.com/Phoneboothmumbai/heycharu.git
cd heycharu
```

---

## Step 4: Setup Backend

```bash
cd /home/heycharu/heycharu/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install emergent integrations (for AI)
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# Create .env file
nano .env
```

**Add to backend/.env:**
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=salesbrain
JWT_SECRET=your-super-secure-jwt-secret-change-this-in-production
EMERGENT_LLM_KEY=your-emergent-llm-key-here
WA_SERVICE_URL=http://localhost:3001
```

**Test backend:**
```bash
# Still in venv
uvicorn server:app --host 0.0.0.0 --port 8001
# Press Ctrl+C to stop after confirming it works
```

---

## Step 5: Setup Frontend

```bash
cd /home/heycharu/heycharu/frontend

# Install dependencies
yarn install

# Create .env file
nano .env
```

**Add to frontend/.env:**
```
REACT_APP_BACKEND_URL=https://yourdomain.com
```
*(Replace with your actual domain or server IP)*

**Build frontend:**
```bash
yarn build
```

---

## Step 6: Setup WhatsApp Service

```bash
cd /home/heycharu/heycharu/whatsapp-service

# Install dependencies
npm install

# Create .env file (optional - uses defaults)
nano .env
```

**Add to whatsapp-service/.env:**
```
BACKEND_URL=http://localhost:8001
WA_PORT=3001
```

---

## Step 7: Setup PM2 Process Manager

Create PM2 ecosystem file:

```bash
cd /home/heycharu/heycharu
nano ecosystem.config.js
```

**Add this content:**
```javascript
module.exports = {
  apps: [
    {
      name: 'backend',
      cwd: '/home/heycharu/heycharu/backend',
      script: 'venv/bin/uvicorn',
      args: 'server:app --host 0.0.0.0 --port 8001',
      interpreter: 'none',
      env: {
        MONGO_URL: 'mongodb://localhost:27017',
        DB_NAME: 'salesbrain'
      }
    },
    {
      name: 'whatsapp-service',
      cwd: '/home/heycharu/heycharu/whatsapp-service',
      script: 'index.js',
      interpreter: 'node',
      env: {
        BACKEND_URL: 'http://localhost:8001',
        WA_PORT: '3001'
      }
    }
  ]
};
```

**Start services:**
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
# Run the command it outputs (with sudo)
```

**Check status:**
```bash
pm2 status
pm2 logs
```

---

## Step 8: Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/heycharu
```

**Add this configuration:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;  # Replace with your domain or server IP

    # Frontend - serve static files
    location / {
        root /home/heycharu/heycharu/frontend/build;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # WhatsApp Service (internal only, optional)
    location /wa {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

**Enable the site:**
```bash
sudo ln -s /etc/nginx/sites-available/heycharu /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

---

## Step 9: Setup SSL with Let's Encrypt (Recommended)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
# Follow the prompts

# Auto-renewal is set up automatically
sudo certbot renew --dry-run  # Test renewal
```

---

## Step 10: Configure Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

---

## Step 11: Seed Initial Data (Optional)

```bash
curl -X POST http://localhost:8001/api/seed
```

---

## Step 12: Access Your Application

1. Open browser: `https://yourdomain.com` (or `http://YOUR_SERVER_IP`)
2. Register a new account
3. Go to WhatsApp page → Scan QR code with your phone
4. Start receiving messages!

---

## Useful Commands

### Check service status
```bash
pm2 status
pm2 logs backend
pm2 logs whatsapp-service
```

### Restart services
```bash
pm2 restart all
# or individually
pm2 restart backend
pm2 restart whatsapp-service
```

### Update code from GitHub
```bash
cd /home/heycharu/heycharu
git pull origin main

# Rebuild frontend if changed
cd frontend && yarn build

# Restart services
pm2 restart all
```

### View MongoDB
```bash
mongosh
use salesbrain
db.customers.find().pretty()
```

### Check logs
```bash
pm2 logs
sudo tail -f /var/log/nginx/error.log
```

---

## Troubleshooting

### Backend won't start
```bash
cd /home/heycharu/heycharu/backend
source venv/bin/activate
python -c "import server"  # Check for import errors
```

### MongoDB connection issues
```bash
sudo systemctl status mongod
sudo journalctl -u mongod
```

### Nginx errors
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

### WhatsApp QR not showing
```bash
pm2 logs whatsapp-service
# Make sure Baileys dependencies are installed
cd /home/heycharu/heycharu/whatsapp-service && npm install
```

---

## Security Recommendations

1. **Change default passwords** in .env files
2. **Enable MongoDB authentication** for production
3. **Keep server updated**: `sudo apt update && sudo apt upgrade`
4. **Setup fail2ban**: `sudo apt install fail2ban`
5. **Regular backups** of MongoDB data

---

## MongoDB Backup (Recommended)

```bash
# Create backup script
nano /home/heycharu/backup.sh
```

```bash
#!/bin/bash
mongodump --db salesbrain --out /home/heycharu/backups/$(date +%Y%m%d)
find /home/heycharu/backups -type d -mtime +7 -exec rm -rf {} +
```

```bash
chmod +x /home/heycharu/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /home/heycharu/backup.sh
```

---

## Done! 🎉

Your Sales Brain application should now be running on your Vultr server.

**Test Credentials (after seeding):**
- Create a new account via the Register page
- Or use API: `curl -X POST https://yourdomain.com/api/auth/register -H "Content-Type: application/json" -d '{"email":"admin@example.com","password":"secure123","name":"Admin","role":"admin"}'
