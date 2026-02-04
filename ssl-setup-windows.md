# SSL Certificate Setup for j-ai.top on Windows

## Option 1: Using WSL2 (Recommended)

### 1. Install WSL2
```powershell
# Run as Administrator
wsl --install
# Choose Ubuntu when prompted
```

### 2. Setup Ubuntu and Install Certbot
```bash
# In WSL2 Ubuntu terminal
sudo apt update
sudo apt install -y certbot python3-certbot-nginx nginx

# Install Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 3. Copy Nginx Config
```bash
# Copy the config file to Ubuntu
# From Windows PowerShell:
wsl cp /mnt/c/Users/Abdul\ Rahman/Documents/JAI_Assistant/nginx-jai-top.conf /tmp/

# In WSL2 Ubuntu:
sudo cp /tmp/nginx-jai-top.conf /etc/nginx/sites-available/j-ai-top
sudo ln -s /etc/nginx/sites-available/j-ai-top /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Get SSL Certificate
```bash
# Make sure DNS is pointing to your server first!
sudo certbot --nginx -d j-ai.top -d www.j-ai.top
```

## Option 2: Using Windows Native SSL (Self-Signed)

### Install Chocolatey (if not installed)
```powershell
# Run as Administrator
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

### Install mkcert for local SSL
```powershell
choco install mkcert
mkcert -install
mkcert j-ai.top localhost 127.0.0.1 ::1
```

### Windows IIS Configuration
```powershell
# Install IIS
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServer
Enable-WindowsOptionalFeature -Online -FeatureName IIS-CommonHttpFeatures
Enable-WindowsOptionalFeature -Online -FeatureName IIS-HttpErrors
Enable-WindowsOptionalFeature -Online -FeatureName IIS-HttpLogging
Enable-WindowsOptionalFeature -Online -FeatureName IIS-StaticContent
Enable-WindowsOptionalFeature -Online -FeatureName IIS-HttpRedirect
Enable-WindowsOptionalFeature -Online -FeatureName IIS-ASPNET45
```

## Option 3: Using Cloudflare (Easiest)

### 1. Sign up for Cloudflare (free tier)
### 2. Add your domain j-ai.top
### 3. Point nameservers to Cloudflare
### 4. Enable SSL/TLS in Cloudflare dashboard
### 5. Set SSL/TLS to "Full (strict)"

### Cloudflare SSL Certificate
- No installation needed
- Automatic renewal
- Free SSL certificate
- DDoS protection included

## DNS Configuration Required

Before any SSL setup, ensure your DNS records point to your server:

```
A Record: @ -> YOUR_SERVER_IP
A Record: www -> YOUR_SERVER_IP
AAAA Record: @ -> YOUR_IPV6_ADDRESS (if available)
AAAA Record: www -> YOUR_IPV6_ADDRESS (if available)
```

## Testing SSL Certificate

After installation, test your SSL:
```bash
# Test SSL configuration
curl -I https://j-ai.top

# Check certificate details
openssl s_client -connect j-ai.top:443 -servername j-ai.top
```

## Auto-Renewal Setup (WSL2/Certbot)

```bash
# Setup automatic renewal
sudo crontab -e
# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet
```

## Port Forwarding (if behind router)

Forward these ports to your server:
- Port 80 (HTTP)
- Port 443 (HTTPS)

## Firewall Rules (Windows)

```powershell
# Run as Administrator
New-NetFirewallRule -DisplayName "JAI HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
New-NetFirewallRule -DisplayName "JAI HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow
```
