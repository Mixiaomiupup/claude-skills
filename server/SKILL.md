---
name: server
description: Use when user mentions server, deployment, remote access, SSH, or needs to connect to cloud/remote machines. Also use when deploying projects, checking server status, or managing services. Machines are called 云机 (cloud), 新云机 (new cloud), 大机 (big ECS), U机 (Ubuntu), C机 (CS2 Quantix), W机 (Windows).
---

# Machines Overview

| 代号 | 角色 | Access |
| ---- | ---- | ------ |
| **云机** | Web 托管, frps 中继 (U机/W机) | `ssh root@YOUR_SERVER_IP` |
| **新云机** | Web 托管, frps 中继 (C机) | `sshpass -p 'chenhui' ssh root@47.97.153.197` |
| **大机** | 高性能计算 (32C/245G) | `sshpass -p 'Huazhiai123' ssh root@8.147.115.151` |
| **U机** | 重计算任务 (采集/训练) | `ssh -p 6000 mixiaomi@YOUR_SERVER_IP` (via frp) |
| **C机** | CS2 Quantix 独立部署 | `sshpass -p 'chenhui' ssh -p 6001 chenhui@47.97.153.197` (via frp) |
| **W机** | 待定 | `sshpass -p 'huazhi1' ssh -p 6001 huazhi1@YOUR_SERVER_IP` (via frp) |

---

# 1. 云机（Aliyun 轻量应用服务器）

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
| csfilter (CS2 饰品量化分析)      | nginx 反代到U机       | -                      | nginx `/csfilter/` → U机:5001       |

> **注意**: csfilter 实际运行在U机上，云机仅做 nginx 反向代理。见下方U机部分。

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

> csfilter 实际部署在U机上，不在云机。操作详见下方U机部分。

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

# 2. 大机（Aliyun ECS 高性能实例）

China North 2 (Beijing) Ubuntu ECS instance, 32核高性能机器。

## Connection

| Field      | Value                                              |
| ---------- | -------------------------------------------------- |
| Host       | `8.147.115.151`                                    |
| Private IP | `172.25.63.72`                                     |
| User       | `root`                                             |
| Password   | `Huazhiai123`                                      |
| SSH        | `sshpass -p 'Huazhiai123' ssh root@8.147.115.151`  |

## Specs

| Item          | Detail                             |
| ------------- | ---------------------------------- |
| Instance ID   | `i-2ze8v3zn0e4m92zqhc01`          |
| OS            | Ubuntu 22.04 64位                  |
| Kernel        | 5.15.0-173-generic                 |
| CPU           | 32 vCPU (x86_64)                   |
| Memory        | 245 GiB                            |
| Disk          | 40 GiB                             |
| Bandwidth     | 1 Mbps                             |
| Expires       | 2026-05-03                         |
| Region        | 华北2（北京）                       |

## Deployed Projects

| Project | Web Root | Port |
| ------- | -------- | ---- |
| (暂无)  | -        | -    |

## Common Operations

```bash
# SSH connect
sshpass -p 'Huazhiai123' ssh -o StrictHostKeyChecking=no root@8.147.115.151

# Run remote command
sshpass -p 'Huazhiai123' ssh root@8.147.115.151 "command here"
```

## Notes

- 32核 245GB 内存，适合大规模计算任务
- 磁盘仅 40GB，如需更多空间需挂载数据盘
- 公网带宽 1Mbps，传输大文件较慢
- 新实例，环境待初始化

---

# 4. U机（Ubuntu 工作站，via frp）

无公网 IP 的内网机器，通过 frp 穿透访问。适合跑 headless Chrome 采集等重计算任务。

## Connection

| Field    | Value                                        |
| -------- | -------------------------------------------- |
| SSH      | `ssh -p 6000 mixiaomi@YOUR_SERVER_IP`         |
| 穿透方式 | frpc → 云机 frps (port 7000)                 |
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
# 推送文件到U机（从本地 Mac 执行）
scp -P 6000 path/to/file mixiaomi@YOUR_SERVER_IP:/home/mixiaomi/projects/csfilter/path/to/file
```

## CSFilter 部署

csfilter 的实际运行环境在U机上（不在云机）。

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

- 无公网 IP，依赖 frp 穿透（frpc → 云机 frps:7000 → port 6000）
- frpc 断线需重连，配置为 systemd 服务开机自启
- 比云机 2C2G 性能强很多，适合跑 Chrome 采集、数据处理等任务
- **已安装**: gh, python3, chrome, chromedriver, sqlite3(未安装)

---

# 5. W机（Windows 工作站，via frp）

无公网 IP 的内网 Windows 机器，通过 frp 穿透访问。

## Connection

| Field    | Value                                                |
| -------- | ---------------------------------------------------- |
| SSH      | `sshpass -p 'huazhi1' ssh -p 6001 huazhi1@YOUR_SERVER_IP` |
| 穿透方式 | frpc → 云机 frps (port 7000) → port 6001             |
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

---

# 6. 新云机（Aliyun ECS - C机中继）

C机的 frps 中继 + nginx 反代，独立于云机。

## Connection

| Field    | Value                                                              |
| -------- | ------------------------------------------------------------------ |
| Host     | `47.97.153.197`                                                    |
| User     | `root`                                                             |
| Password | `chenhui`                                                          |
| SSH      | `sshpass -p 'chenhui' ssh -o PubkeyAuthentication=no -o PreferredAuthentications=keyboard-interactive,password root@47.97.153.197` |

> **注意**: 此机器需要 `-o PreferredAuthentications=keyboard-interactive,password` 才能密码登录。

## Specs

| Item     | Detail                       |
| -------- | ---------------------------- |
| Hostname | iZbp14vi4g4834c8vrnf6fZ     |
| OS       | Ubuntu 24.04.2 LTS           |
| CPU      | 2 vCPU                       |
| Memory   | 1.6 GiB                      |
| Disk     | 40 GiB                       |

## Services

### frps (frp 服务端)

```bash
# config: /etc/frp/frps.toml
# bindPort = 7000, auth.token = "csfilter2026frp"
# Dashboard: http://47.97.153.197:7500 (admin/admin123)

sshpass -p 'chenhui' ssh root@47.97.153.197 "systemctl status frps"
```

### nginx (反向代理)

| URL Path        | 行为                         |
| --------------- | ---------------------------- |
| `/`             | 302 重定向到 `/cs2quantix/`  |
| `/cs2quantix/`  | 反向代理到 C机:5001          |

```bash
# config: /etc/nginx/sites-available/csfilter
sshpass -p 'chenhui' ssh root@47.97.153.197 "cat /etc/nginx/sites-available/csfilter"
```

## UFW Ports

22, 80, 443, 5001, 6001, 6002, 7000, 7500

## Notes

- 仅做 frps 中继 + nginx 反代，不跑业务
- C机通过 frpc → 新云机 frps:7000 → port 6001 (SSH) / port 5001 (web)
- 公网访问 CS2 Quantix: http://47.97.153.197/cs2quantix/

---

# 7. C机（Lenovo Gaming 工作站，via frp）

CS2 Quantix 独立部署，通过新云机 frp 穿透访问。

## Connection

| Field    | Value                                                          |
| -------- | -------------------------------------------------------------- |
| SSH      | `sshpass -p 'chenhui' ssh -p 6001 -o PubkeyAuthentication=no -o PreferredAuthentications=keyboard-interactive,password chenhui@47.97.153.197` |
| 穿透方式 | frpc → 新云机 frps (port 7000) → port 6001                    |
| User     | `chenhui`                                                      |
| Password | `chenhui`                                                      |

## Specs

| Item     | Detail                               |
| -------- | ------------------------------------ |
| Hostname | chenhui-Lenovo-Gaming                |
| OS       | Ubuntu 24.04.4 LTS                   |
| CPU      | Intel i7-4720HQ (8 threads, 2.6GHz)  |
| Memory   | 7.6 GiB                              |
| Disk     | 109 GiB                              |
| Role     | CS2 Quantix 独立运行                 |

## CSFilter (CS2 Quantix) 部署

| 项目     | 值                                      |
| -------- | --------------------------------------- |
| App 路径 | `/home/chenhui/projects`                |
| Venv     | `/home/chenhui/projects/.venv`          |
| DB       | `/home/chenhui/projects/database/csqaq.db` |
| Logs     | `/home/chenhui/projects/logs/`          |
| Web      | gunicorn 4 workers, port 5001           |

### Systemd 服务

```bash
# 服务管理
sshpass -p 'chenhui' ssh -p 6001 chenhui@47.97.153.197 "sudo systemctl status csfilter-proxy csfilter-scheduler csfilter-web"

# 查看日志
sshpass -p 'chenhui' ssh -p 6001 chenhui@47.97.153.197 "tail -50 ~/projects/logs/access_app.log"
sshpass -p 'chenhui' ssh -p 6001 chenhui@47.97.153.197 "sudo journalctl -u csfilter-scheduler -n 30 --no-pager"
```

### 更新代码流程

```bash
# 1. 从本地 Mac 推送文件
sshpass -p 'chenhui' scp -P 6001 -o PubkeyAuthentication=no src/web/app.py chenhui@47.97.153.197:/home/chenhui/projects/src/web/app.py

# 2. 重启服务
sshpass -p 'chenhui' ssh -p 6001 chenhui@47.97.153.197 "sudo systemctl restart csfilter-web"
```

## 日志系统

| 日志 | 路径 | 说明 |
| ---- | ---- | ---- |
| gunicorn access | `logs/access.log` | HTTP 请求标准格式 |
| 应用访问 | `logs/access_app.log` | IP、路径、耗时、用户、UA |
| gunicorn error | `logs/error.log` | 启动/错误 |
| 采集日志 | `logs/collect_YYYY-MM-DD.log` | scheduler 采集记录 |

## 通知收件人（独立于U机）

```
2878366733@qq.com, 1872861140@qq.com, 1092493368@qq.com,
954993689@qq.com, 1253706785@qq.com, 952445655@qq.com,
892801936@qq.com, 469482674@qq.com
```

## frpc 配置

```toml
# ~/.config/frp/frpc.toml
serverAddr = "47.97.153.197"
serverPort = 7000
auth.token = "csfilter2026frp"

[[proxies]]
name = "ssh-newbox"
type = "tcp"
localIP = "127.0.0.1"
localPort = 22
remotePort = 6001

[[proxies]]
name = "csfilter-web"
type = "tcp"
localIP = "127.0.0.1"
localPort = 5001
remotePort = 5001
```

## Notes

- 无公网 IP，依赖 frp 穿透（frpc → 新云机 frps:7000）
- 硬件较老（4代i7），采集速度约为U机的 40%
- 站名: CS2 Quantix · 量化智库
- 公网访问: http://47.97.153.197/cs2quantix/
- Chrome 147 + ChromeDriver 147.0.7727.57（手动预填 ~/.wdm/ 缓存）
- sudo 免密已配置: `/etc/sudoers.d/chenhui`
- **已安装**: python3.12, google-chrome, chromedriver, gunicorn, frpc
