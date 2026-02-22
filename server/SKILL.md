---
name: server
description: Use when user mentions server, deployment, remote access, SSH, or needs to connect to their cloud server. Also use when deploying projects, checking server status, or managing services on the remote machine.
---

# Lightweight Application Server

Aliyun (China East 2 - Shanghai) Ubuntu instance for hosting personal projects.

## Connection

| Field | Value |
|-------|-------|
| Host | `YOUR_SERVER_IP` |
| Private IP | `YOUR_PRIVATE_IP` |
| User | `root` |
| Password | `YOUR_PASSWORD_HERE` |
| SSH | `ssh root@YOUR_SERVER_IP` |

## Specs

| Item | Detail |
|------|--------|
| Instance Name | Ubuntu-hgzq |
| Instance ID | `6d822258da29422c9532f3154f8bb0e6` |
| OS | Ubuntu |
| CPU | 2 vCPU |
| Memory | 2 GiB |
| Disk | 40 GiB ESSD |
| Expires | 2027-02-17 |
| Created | 2026-02-16 |

## Deployed Projects

| Project | Web Root | Local Source | Port |
|---------|----------|--------------|------|
| shige-h5 (food personality test) | `/var/www/html/` | `~/projects/shige-h5/` | 80 (nginx) |
| csfilter (CS2 饰品量化分析) | `/opt/csfilter/app/` | `~/csfilter/` | 5001 (gunicorn) → nginx `/csfilter/` |

## Common Operations

```bash
# SSH connect (use sshpass for password auth)
sshpass -p 'YOUR_PASSWORD_HERE' ssh -o StrictHostKeyChecking=no root@YOUR_SERVER_IP

# Deploy static site (example: shige-h5)
cd ~/projects/shige-h5 && npm run build
scp -r dist/* root@YOUR_SERVER_IP:/var/www/html/

# Check nginx status
ssh root@YOUR_SERVER_IP "systemctl status nginx"

# View nginx config
ssh root@YOUR_SERVER_IP "cat /etc/nginx/sites-enabled/default"
```

### CSFilter Operations

```bash
# Service management
sshpass -p 'YOUR_PASSWORD_HERE' ssh root@YOUR_SERVER_IP "systemctl status csfilter-proxy csfilter-scheduler csfilter-web"

# Update code
sshpass -p 'YOUR_PASSWORD_HERE' ssh root@YOUR_SERVER_IP "systemctl stop csfilter-scheduler csfilter-web && cd /opt/csfilter/app && sudo -u csfilter git pull origin main && sudo -u csfilter /opt/csfilter/app/.venv/bin/pip install -r requirements.txt && systemctl start csfilter-scheduler csfilter-web"

# View logs
sshpass -p 'YOUR_PASSWORD_HERE' ssh root@YOUR_SERVER_IP "tail -50 /var/log/csfilter/scheduler.log"

# Service user: csfilter
# App path: /opt/csfilter/app
# Venv: /opt/csfilter/app/.venv
# DB: /opt/csfilter/app/database/csqaq.db (WAL mode)
# Backups: /opt/csfilter/backups/ (daily 3AM, 7-day retention)
# Logs: /var/log/csfilter/
```

## Notes

- Accessible within mainland China (no GFW issues)
- Web server: nginx (static + reverse proxy)
- 1GB swap configured (vm.swappiness=10)
- UFW firewall: only 22, 80, 443 exposed
- Add new projects to the "Deployed Projects" table above
