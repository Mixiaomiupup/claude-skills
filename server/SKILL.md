---
name: server
description: Use when user mentions server, deployment, remote access, SSH, or needs to connect to their cloud server. Also use when deploying projects, checking server status, or managing services on the remote machine.
---

# Lightweight Application Server

Aliyun (China East 2 - Shanghai) Ubuntu instance for hosting personal projects.

## Connection

| Field | Value |
|-------|-------|
| Host | `106.15.125.84` |
| Private IP | `172.24.17.232` |
| User | `root` |
| Password | `mi954993689..` |
| SSH | `ssh root@106.15.125.84` |

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
sshpass -p 'mi954993689..' ssh -o StrictHostKeyChecking=no root@106.15.125.84

# Deploy static site (example: shige-h5)
cd ~/projects/shige-h5 && npm run build
scp -r dist/* root@106.15.125.84:/var/www/html/

# Check nginx status
ssh root@106.15.125.84 "systemctl status nginx"

# View nginx config
ssh root@106.15.125.84 "cat /etc/nginx/sites-enabled/default"
```

### CSFilter Operations

```bash
# Service management
sshpass -p 'mi954993689..' ssh root@106.15.125.84 "systemctl status csfilter-proxy csfilter-scheduler csfilter-web"

# Update code
sshpass -p 'mi954993689..' ssh root@106.15.125.84 "systemctl stop csfilter-scheduler csfilter-web && cd /opt/csfilter/app && sudo -u csfilter git pull origin main && sudo -u csfilter /opt/csfilter/app/.venv/bin/pip install -r requirements.txt && systemctl start csfilter-scheduler csfilter-web"

# View logs
sshpass -p 'mi954993689..' ssh root@106.15.125.84 "tail -50 /var/log/csfilter/scheduler.log"

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
