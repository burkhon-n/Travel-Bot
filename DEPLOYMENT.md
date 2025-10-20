# 🚀 Deployment Guide - Travel Bot

Complete guide for deploying the Travel Bot to production.

## 📋 Pre-Deployment Checklist

- [ ] All features tested locally
- [ ] Database backup strategy in place
- [ ] Environment variables documented
- [ ] Google OAuth redirect URIs configured
- [ ] Bot commands registered with BotFather
- [ ] Admin accounts configured
- [ ] Error monitoring setup (optional but recommended)

## 🏗️ Deployment Options

### Option 1: VPS/Cloud Server (Recommended)

**Best for**: Full control, scalability, production use

**Providers**: DigitalOcean, AWS EC2, Google Cloud, Linode, Vultr

#### Server Requirements
- **OS**: Ubuntu 20.04+ or similar
- **RAM**: 1GB minimum, 2GB recommended
- **CPU**: 1 core minimum
- **Storage**: 20GB minimum
- **Python**: 3.8+
- **PostgreSQL**: 12+

#### Setup Steps

1. **Provision Server**
   ```bash
   # Connect to your server
   ssh user@your-server-ip
   ```

2. **Update System**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

3. **Install Dependencies**
   ```bash
   sudo apt install python3-pip python3-venv nginx certbot python3-certbot-nginx postgresql -y
   ```

4. **Create Application User**
   ```bash
   sudo useradd -m -s /bin/bash travelbot
   sudo su - travelbot
   ```

5. **Clone Repository**
   ```bash
   cd ~
   git clone <your-repository-url> travel-bot
   cd travel-bot
   ```

6. **Setup Python Environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

7. **Configure Environment**
   ```bash
   nano .env
   ```
   
   Add production values:
   ```env
   BOT_TOKEN=your_bot_token
   BOT_USERNAME=putravelbot
   URL=https://your-domain.com
   
   # Production Database
   DATABASE_URL=postgresql://user:password@localhost:5432/travel_bot
   
   # Google OAuth
   CLIENT_ID=your_client_id
   CLIENT_SECRET=your_client_secret
   OAUTH_REDIRECT_URI=https://your-domain.com/auth/callback
   
   ADMINS=123456789,987654321
   ```

8. **Setup PostgreSQL Database**
   ```bash
   sudo -u postgres psql
   ```
   
   In PostgreSQL:
   ```sql
   CREATE DATABASE travel_bot;
   CREATE USER travelbot WITH PASSWORD 'strong_password';
   GRANT ALL PRIVILEGES ON DATABASE travel_bot TO travelbot;
   \q
   ```
   
   Update `.env` with database credentials.

9. **Initialize Database**
   ```bash
   source .venv/bin/activate
   python scripts/reset_db.py
   ```

10. **Setup Systemd Service**
    ```bash
    sudo nano /etc/systemd/system/travelbot.service
    ```
    
    Add:
    ```ini
    [Unit]
    Description=Travel Bot - Telegram Bot Service
    After=network.target postgresql.service
    
    [Service]
    Type=simple
    User=travelbot
    WorkingDirectory=/home/travelbot/travel-bot
    Environment="PATH=/home/travelbot/travel-bot/.venv/bin"
    ExecStart=/home/travelbot/travel-bot/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
    Restart=always
    RestartSec=10
    
    [Install]
    WantedBy=multi-user.target
    ```
    
    Enable and start:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable travelbot
    sudo systemctl start travelbot
    sudo systemctl status travelbot
    ```

11. **Setup Nginx Reverse Proxy**
    ```bash
    sudo nano /etc/nginx/sites-available/travelbot
    ```
    
    Add:
    ```nginx
    server {
        listen 80;
        server_name your-domain.com;
        
        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    ```
    
    Enable site:
    ```bash
    sudo ln -s /etc/nginx/sites-available/travelbot /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl restart nginx
    ```

12. **Setup SSL with Let's Encrypt**
    ```bash
    sudo certbot --nginx -d your-domain.com
    ```
    
    Follow prompts to configure SSL.

13. **Update Google OAuth**
    - Go to Google Cloud Console
    - Add redirect URI: `https://your-domain.com/auth/callback`
    - Add JavaScript origin: `https://your-domain.com`

14. **Set Telegram Webhook**
    ```bash
    curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
         -H "Content-Type: application/json" \
         -d '{"url": "https://your-domain.com/webhook"}'
    ```
    
    Verify:
    ```bash
    curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
    ```

15. **Test Deployment**
    - Open bot in Telegram
    - Test registration flow
    - Test trip creation
    - Test receipt upload
    - Test admin dashboard

### Option 2: Heroku (Easy but Limited)

**Best for**: Quick deployment, testing

#### Setup Steps

1. **Install Heroku CLI**
   ```bash
   curl https://cli-assets.heroku.com/install.sh | sh
   heroku login
   ```

2. **Create Heroku App**
   ```bash
   heroku create your-app-name
   ```

3. **Add PostgreSQL**
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

4. **Set Environment Variables**
   ```bash
   heroku config:set BOT_TOKEN=your_token
   heroku config:set BOT_USERNAME=putravelbot
   heroku config:set CLIENT_ID=your_client_id
   heroku config:set CLIENT_SECRET=your_client_secret
   heroku config:set ADMINS=123456789
   # DATABASE_URL is auto-set by Heroku
   ```

5. **Create Procfile**
   ```bash
   echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile
   ```

6. **Deploy**
   ```bash
   git push heroku main
   ```

7. **Initialize Database**
   ```bash
   heroku run python scripts/reset_db.py
   ```

8. **Set Webhook**
   ```bash
   curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
        -d "url=https://your-app-name.herokuapp.com/webhook"
   ```

### Option 3: Docker (Containerized)

**Best for**: Consistent environments, CI/CD

#### Dockerfile

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### docker-compose.yml

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - BOT_USERNAME=${BOT_USERNAME}
      - DATABASE_URL=postgresql://travelbot:password@db:5432/travel_bot
      - CLIENT_ID=${CLIENT_ID}
      - CLIENT_SECRET=${CLIENT_SECRET}
      - OAUTH_REDIRECT_URI=${OAUTH_REDIRECT_URI}
      - ADMINS=${ADMINS}
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=travel_bot
      - POSTGRES_USER=travelbot
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

#### Deploy with Docker

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Initialize database
docker-compose exec app python scripts/reset_db.py

# Stop
docker-compose down
```

## 🔒 Security Hardening

### 1. Firewall Configuration
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 2. Secure PostgreSQL
```bash
sudo nano /etc/postgresql/*/main/pg_hba.conf
```
Change to:
```
local   all             all                                     md5
host    all             all             127.0.0.1/32            md5
```

### 3. Environment Variables
- Never commit `.env` to git
- Use secrets management in production
- Rotate secrets regularly

### 4. Regular Updates
```bash
# Create update script
cat > ~/update-travelbot.sh << 'EOF'
#!/bin/bash
cd /home/travelbot/travel-bot
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart travelbot
EOF

chmod +x ~/update-travelbot.sh
```

## 📊 Monitoring

### Application Logs
```bash
# Systemd service logs
sudo journalctl -u travelbot -f

# Application logs (if configured)
tail -f /home/travelbot/travel-bot/logs/app.log
```

### Database Monitoring
```bash
# Check connections
sudo -u postgres psql -d travel_bot -c "SELECT count(*) FROM pg_stat_activity;"

# Check database size
sudo -u postgres psql -d travel_bot -c "SELECT pg_size_pretty(pg_database_size('travel_bot'));"
```

### System Resources
```bash
htop  # Install: sudo apt install htop
```

## 🔄 Backup Strategy

### Database Backup Script
```bash
cat > ~/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/travelbot/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

pg_dump -U travelbot travel_bot | gzip > $BACKUP_DIR/travel_bot_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "travel_bot_*.sql.gz" -mtime +7 -delete
EOF

chmod +x ~/backup-db.sh
```

### Automated Backups (Cron)
```bash
crontab -e
```

Add:
```cron
# Backup database daily at 2 AM
0 2 * * * /home/travelbot/backup-db.sh
```

## 🆘 Troubleshooting

### Bot Not Responding
1. Check service status: `sudo systemctl status travelbot`
2. View logs: `sudo journalctl -u travelbot -n 50`
3. Verify webhook: `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo`

### Database Connection Issues
1. Check PostgreSQL: `sudo systemctl status postgresql`
2. Test connection: `psql -U travelbot -d travel_bot`
3. Check DATABASE_URL in `.env`

### OAuth Errors
1. Verify redirect URIs in Google Console
2. Check OAUTH_REDIRECT_URI in `.env`
3. Ensure SSL certificate valid

### Performance Issues
1. Check system resources: `htop`
2. Analyze database queries
3. Review application logs
4. Consider adding Redis for caching

## 📝 Post-Deployment Checklist

- [ ] Application running and accessible
- [ ] Webhook set and verified
- [ ] SSL certificate installed and valid
- [ ] Database backups configured
- [ ] Monitoring in place
- [ ] Error alerts configured
- [ ] Documentation updated
- [ ] Admin access tested
- [ ] User flow tested end-to-end
- [ ] Performance benchmarked

## 🎉 Go Live!

Your bot is now live at `https://your-domain.com` and ready for users!

---

**Need Help?** Refer to the main README.md for additional information.
