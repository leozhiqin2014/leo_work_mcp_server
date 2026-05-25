Leo MCP Server 部署与使用指南
================================

基于 FastMCP 的 HTTP MCP 服务器，提供家庭成员上下文记录的管理工具，使用 MySQL 持久化、可选腾讯云 COS 存储图片/文件，并通过 Bearer JWT (RSA) 进行鉴权。

## 项目结构

```
leo_work_mcp_server/
├── server.py                 # 入口：创建 FastMCP 实例、注册工具、HTTP 模式启动
├── generate_keys.py          # 生成 RSA 密钥对、签发客户端 JWT、写出 client_config.json / .env
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── tools/                    # MCP 工具实现
│   └── member_context.py     # 成员上下文工具
├── dao/                      # 数据访问层（PyMySQL）
│   ├── db.py                 # 数据库连接配置（环境变量驱动）
│   ├── member_context_dao.py
│   ├── member_info_dao.py
│   ├── context_category_dao.py
│   └── tag_dao.py
├── models/
│   └── member_context.py     # 上下文实体模型与枚举
├── utils/
│   └── cos_helper.py         # COS 预签名下载链接生成
├── sql/                      # 建表与初始化数据 SQL
│   ├── member_info.sql
│   ├── member_context.sql
│   ├── context_category.sql
│   ├── context_category_data.sql
│   ├── tag.sql
│   └── tag_data.sql
├── systemd/
│   └── leo-mcp.service       # systemd 服务单元
├── keys/                     # generate_keys.py 生成（不要提交到 git）
│   ├── private.pem
│   └── public.pem
└── client_config.json        # generate_keys.py 生成，含客户端 Token
```

---

## 一、环境变量

服务通过环境变量读取配置，未设置时使用默认值。

### 服务运行
| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MCP_HOST` | `0.0.0.0` | 监听地址 |
| `MCP_PORT` | `9100` | 监听端口（与 `leo_mcp_server` 同机部署时已避开其默认 8000） |
| `MCP_JWT_ENABLED` | `true` | 是否启用 JWT 鉴权 |
| `MCP_ISSUER` | `leo-mcp-server` | JWT issuer，需与签发端一致 |
| `MCP_AUDIENCE` | `mcp-clients` | JWT audience，需与签发端一致 |
| `MCP_PUBLIC_KEY_PATH` | `keys/public.pem` | 公钥文件路径 |
| `MCP_PUBLIC_KEY` | — | 直接传入公钥内容（路径不存在时使用） |

### 数据库（MySQL）
| 变量 | 默认值 |
|------|--------|
| `DB_HOST` | `127.0.0.1` |
| `DB_PORT` | `3306` |
| `DB_USER` | `root` |
| `DB_PASSWORD` | 空（必须通过环境变量注入） |
| `DB_NAME` | `work_data` |

### 腾讯云 COS（图片/文件预签名下载链接，可选）
| 变量 | 默认值 |
|------|--------|
| `COS_SECRET_ID` | 空 |
| `COS_SECRET_KEY` | 空 |
| `COS_BUCKET` | 空 |
| `COS_REGION` | `ap-beijing` |

未配置 COS 时，图片/文件记录的 `download_url` 字段返回空字符串，不影响其他功能。

---

## 二、初始化数据库

按顺序执行 `sql/` 目录下的脚本（默认数据库名 `work_data`）：

```bash
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p work_data < sql/member_info.sql
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p work_data < sql/member_context.sql
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p work_data < sql/context_category.sql
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p work_data < sql/context_category_data.sql
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p work_data < sql/tag.sql
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p work_data < sql/tag_data.sql
```

---

## 三、生成密钥与客户端 Token

```bash
python generate_keys.py
```

执行后生成：
- `keys/private.pem`、`keys/public.pem`（RSA 2048）
- `client_config.json`（含 365 天有效期的 JWT Token）
- `.env`（服务端环境变量样例）

服务端只需 `keys/public.pem`；私钥仅用于本地签发新 Token，不要部署到服务器。

---

## 四、服务端部署

### 方式 A：直接运行

```bash
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

### 方式 B：systemd（生产环境推荐）

`systemd/leo-mcp.service` 默认从 `/opt/leo-mcp-server/.env` 读取环境变量、使用 `mcpuser` 运行：

```bash
sudo useradd -r -s /bin/false mcpuser
sudo cp -r . /opt/leo-mcp-server
sudo chown -R mcpuser:mcpuser /opt/leo-mcp-server

cd /opt/leo-mcp-server
sudo -u mcpuser python -m venv venv
sudo -u mcpuser ./venv/bin/pip install -r requirements.txt

sudo cp systemd/leo-mcp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now leo-mcp
sudo journalctl -u leo-mcp -f
```

### 方式 C：Docker Compose

`docker-compose.yml` 中默认将容器内 `9100` 端口暴露到宿主，并设置 `MCP_PORT=9100`，容器名 `leo-work-mcp-server`，与同机部署的 `leo_mcp_server`（默认 8000）互不冲突。

```bash
python generate_keys.py        # 先生成密钥
docker compose up -d
docker logs -f leo-work-mcp-server
```

> 注意：Dockerfile 中 `EXPOSE 9100` 仅作声明，实际端口以 `MCP_PORT` 与 `docker-compose.yml` 端口映射为准。

### 防火墙

```bash
sudo ufw allow 9100/tcp                                # ufw
sudo firewall-cmd --permanent --add-port=9100/tcp      # firewalld
sudo firewall-cmd --reload
```

---

## 五、客户端配置

服务端默认走 FastMCP 3.x 的 streamable-http，端点路径为 `/mcp/`。

### Claude Desktop / Cursor

```json
{
  "mcpServers": {
    "leo-work-mcp": {
      "url": "http://your-server-ip:9100/mcp/",
      "transport": "http",
      "headers": {
        "Authorization": "Bearer <client_config.json 中的 token>"
      }
    }
  }
}
```

将 `client_config.json` 中的 `server_url` 替换为实际服务器 IP 和端口即可。

---

## 六、内置 MCP 工具

### 成员上下文（`tools/member_context.py`）

| 工具 | 说明 |
|------|------|
| `save_member_context` | 新增或更新上下文记录。传 `record_id` 走更新（仅更新非空字段）；纯文本只需 `content`；上传图片/文件需同时传入 `cos_url`、`cos_key`、`file_name`、`file_size`，按文件后缀自动判定 `IMAGE`/`FILE`。新增时校验昵称必须存在于 `member_info`；1 级 + 2 级分类必须存在于 `context_category`；3 级、4 级分类不存在时自动写入字典表；标签按逗号拆分并写入 `tag` 字典表 |
| `query_member_context` | 按 `record_id` 精确查询，或按昵称/名称 + 多级分类条件分页查询；图片/文件记录自动附加 5 分钟有效的 COS 预签名下载链接 |
| `get_member_context_summary` | 汇总某成员所有不重复的四级分类路径与每个分类下的记录数量，同时返回扁平列表与树形结构 |
| `list_members` | 返回 `member_info` 中所有 `status=1` 的昵称列表 |
| `list_context_categories` | 返回完整分类列表（按一/二级分组），并附带分类约束规则说明 |

### 服务器自带工具（`server.py`）

| 工具 | 说明 |
|------|------|
| `calculate` | 安全计算数学表达式，仅支持 `+ - * / **` 与一元正负 |
| `list_tools` | 列出当前注册的工具（依赖 FastMCP 内部属性，可能在版本变更后失效） |

---

## 七、数据模型概要

- **member_info**：家庭成员档案，`member_nickname` 为唯一标识
- **member_context**：上下文记录主表，`content_format` 区分文字（1）/图片（2）/文件（3），`status` 软删除（1 正常 / 2 删除 / 3 归档），`permission`（1 私有 / 2 家庭可见 / 3 全部可编辑），`tags` 为逗号分隔字符串
- **context_category**：四级分类字典表，`(level_one, level_two, level_three, level_four)` 唯一
- **tag**：标签字典表，`name` 唯一

枚举值参见 `models/member_context.py` 中的 `ContentFormat` / `ContextStatus` / `ContextPermission`。
