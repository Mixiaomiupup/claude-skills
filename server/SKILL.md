---
name: server
description: Use when user mentions server, deployment, remote access, SSH, or needs to connect to their cloud server. Also use when deploying projects, checking server status, or managing services on the remote machine.
---

# Machines Overview

| Machine | Role | Access |
| ------- | ---- | ------ |
| Aliyun 轻量服务器 | Web hosting, frps relay | `ssh root@YOUR_SERVER_IP` |
| 个人PC (Ubuntu) | 重计算任务 (采集/训练) | `ssh -p 6000 mixiaomi@YOUR_SERVER_IP` (via frp) |
| 个人PC (Windows) | 待定 | `sshpass -p 'huazhi1' ssh -p 6001 huazhi1@YOUR_SERVER_IP` (via frp) |

---

# 1. Aliyun 轻量应用服务器

China East 2 (Shanghai) Ubuntu instance for hosting personal projects.

## Connection

| Field      | Value                    |
| ---------- | ------------------------ |
| Host       | `YOUR_SERVER_IP`          |
| Private IP | `YOUR_PRIVATE_IP`          |
| User       | `root`                   |
| Password   | `YOUR_PASSWORD_HERE`          |
| SSH        | `ssh root@YOUR_SERVER_IP` |

## Specs

| Item          | Detail                             |
| ------------- | ---------------------------------- |
| Instance Name | Ubuntu-hgzq                        |
| Instance ID   | `6d822258da29422c9532f3154f8bb0e6` |
| OS            | Ubuntu                             |
| CPU           | 2 vCPU                             |
| Memory        | 2 GiB                              |
| Disk          | 40 GiB ESSD                        |
| Expires       | 2027-02-17                         |
| Created       | 2026-02-16                         |

## Deployed Projects

| Project                          | Web Root               | Local Source           | Port                                 |
| -------------------------------- | ---------------------- | ---------------------- | ------------------------------------ |
| shige-h5 (food personality test) | `/var/www/html/shige/` | `~/projects/shige-h5/` | 80 (nginx) → `/shige`                |
| csfilter (CS2 饰品量化分析)      | nginx 反代到工作站     | -                      | nginx `/csfilter/` → 工作站:5001     |

> **注意**: csfilter 实际运行在个人PC上，Aliyun 仅做 nginx 反向代理。见下方工作站部分。

## Common Operations

```bash
# SSH connect (use sshpass for password auth)
sshpass -p 'YOUR_PASSWORD_HERE' ssh -o StrictHostKeyChecking=no root@YOUR_SERVER_IP

# Deploy static site (example: shige-h5)
cd ~/projects/shige-h5 && npm run build
scp -r dist/* root@YOUR_SERVER_IP:/var/www/html/shige/

# Check nginx status
ssh root@YOUR_SERVER_IP "systemctl status nginx"

# View nginx config
ssh root@YOUR_SERVER_IP "cat /etc/nginx/sites-enabled/default"
```

### CSFilter Operations

> csfilter 实际部署在个人PC上，不在 Aliyun。操作详见下方「个人PC - CSFilter」部分。

## Nginx Routing Rules

每个项目独占一个 URL 前缀，主页不暴露内容。

| URL Path     | 行为                           |
| ------------ | ------------------------------ |
| `/`          | 302 重定向到 `/shige/`         |
| `/shige/`    | 静态站（alias + SPA fallback） |
| `/csfilter/` | 反向代理到 gunicorn:5001       |
| 其他路径     | 404                            |

### 添加新项目的 nginx 模板

静态站：

```nginx
location /新项目/ {
    alias /var/www/html/新项目/;
    try_files $uri $uri/ /新项目/index.html;
}
```

反向代理：

```nginx
location /新项目/ {
    proxy_pass http://127.0.0.1:PORT/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Prefix /新项目;
}
```

**注意**: 静态站的 vite/webpack 构建需设置 `base: "/项目名/"`。

## Notes

- Accessible within mainland China (no GFW issues)
- Web server: nginx (static + reverse proxy)
- 1GB swap configured (vm.swappiness=10)
- UFW firewall: 22, 80, 443, 6000, 6001, 7000, 7500 exposed
- Add new projects to the "Deployed Projects" table above

### frp Server (frps)

```bash
# frps config: /etc/frp/frps.toml
# bindPort = 7000, auth.token = "csfilter2026frp"
# Dashboard: http://YOUR_SERVER_IP:7500 (admin/admin123)

# Service management
sshpass -p 'YOUR_PASSWORD_HERE' ssh root@YOUR_SERVER_IP "systemctl status frps"
```

---

# 2. 个人PC (via frp)

无公网 IP 的内网机器，通过 frp 穿透访问。适合跑 headless Chrome 采集等重计算任务。

## Connection

| Field    | Value                                        |
| -------- | -------------------------------------------- |
| SSH      | `ssh -p 6000 mixiaomi@YOUR_SERVER_IP`         |
| 穿透方式 | frpc → Aliyun frps (port 7000)               |
| User     | `mixiaomi`                                   |

## Specs

| Item   | Detail             |
| ------ | ------------------ |
| OS     | Ubuntu 24.04       |
| CPU    | Intel i7-12700     |
| Memory | 16 GiB            |
| GPU    | GTX 1060 5GB       |
| Role   | 计算密集型任务      |

## Git & GitHub

- **已安装 `gh` CLI** (`/usr/bin/gh`)，已登录 Mixiaomiupup 账号
- Git 操作协议: SSH
- **代码不是 git 仓库**：工作站上的项目代码是直接复制的，没有 `.git` 目录
- **更新代码方式**: 使用 `scp` 从本地推送文件，不用 `git pull`

```bash
# 推送文件到工作站（从本地 Mac 执行）
scp -P 6000 path/to/file mixiaomi@YOUR_SERVER_IP:/home/mixiaomi/projects/csfilter/path/to/file
```

## CSFilter 部署

csfilter 的实际运行环境在这台工作站上（不在 Aliyun）。

| 项目 | 值 |
| ---- | -- |
| App 路径 | `/home/mixiaomi/projects/csfilter` |
| Venv | `/home/mixiaomi/projects/csfilter/.venv` |
| DB | `/home/mixiaomi/projects/csfilter/database/csqaq.db` |
| Logs | `/home/mixiaomi/projects/csfilter/logs/` |

### Systemd 服务

```bash
# 服务管理
ssh -p 6000 mixiaomi@YOUR_SERVER_IP "sudo systemctl status csfilter-proxy csfilter-scheduler csfilter-web"

# 停止/启动 scheduler
ssh -p 6000 mixiaomi@YOUR_SERVER_IP "sudo systemctl stop csfilter-scheduler"
ssh -p 6000 mixiaomi@YOUR_SERVER_IP "sudo systemctl start csfilter-scheduler"

# 查看日志
ssh -p 6000 mixiaomi@YOUR_SERVER_IP "tail -50 /home/mixiaomi/projects/csfilter/logs/scheduler.log"
```

### 更新代码流程

```bash
# 1. 从本地 Mac 推送修改的文件
scp -P 6000 run_scheduler.py mixiaomi@YOUR_SERVER_IP:/home/mixiaomi/projects/csfilter/
scp -P 6000 src/collector/mitm_proxy.py mixiaomi@YOUR_SERVER_IP:/home/mixiaomi/projects/csfilter/src/collector/

# 2. SSH 到工作站重启服务
ssh -p 6000 mixiaomi@YOUR_SERVER_IP "sudo systemctl restart csfilter-scheduler"
```

## Common Operations

```bash
# SSH connect (via frp tunnel)
ssh -p 6000 mixiaomi@YOUR_SERVER_IP

# frpc service on this machine
sudo systemctl status frpc
```

## Notes

- 无公网 IP，依赖 frp 穿透（frpc → Aliyun frps:7000 → port 6000）
- frpc 断线需重连，配置为 systemd 服务开机自启
- 比 Aliyun 2C2G 性能强很多，适合跑 Chrome 采集、数据处理等任务
- **已安装**: gh, python3, chrome, chromedriver, sqlite3(未安装)

---

# 3. 个人PC - Windows (via frp)

无公网 IP 的内网 Windows 机器，通过 frp 穿透访问。

## Connection

| Field    | Value                                                |
| -------- | ---------------------------------------------------- |
| SSH      | `sshpass -p 'huazhi1' ssh -p 6001 huazhi1@YOUR_SERVER_IP` |
| 穿透方式 | frpc → Aliyun frps (port 7000) → port 6001          |
| User     | `huazhi1`                                            |
| Password | `huazhi1`                                            |

## Specs

| Item     | Detail                                    |
| -------- | ----------------------------------------- |
| Hostname | HUAZHI1                                   |
| OS       | Windows 11 专业版 (Build 26200)            |
| CPU      | AMD (Family 26 Model 36) ~2000 MHz        |
| Memory   | 30 GiB                                    |
| Role     | 待定                                      |

## Common Operations

```bash
# SSH connect (via frp tunnel)
sshpass -p 'huazhi1' ssh -p 6001 -o StrictHostKeyChecking=no huazhi1@YOUR_SERVER_IP

# Run PowerShell command
sshpass -p 'huazhi1' ssh -p 6001 huazhi1@YOUR_SERVER_IP "powershell -Command 'Get-Process'"
```

## Notes

- 默认 shell 是 CMD，如需 PowerShell 需加 `powershell -Command '...'`
- frpc 配置: `C:\frp\frpc.toml`，remotePort = 6001
- 无公网 IP，依赖 frp 穿透
