"""
密钥对生成脚本
用途：生成 RSA 密钥对，并为客户端生成 JWT Token
运行一次即可，生成的 keys/ 目录和 client_config.json 供后续使用
"""

import json
import os
from datetime import datetime, timedelta

# FastMCP 2.0+ / 3.0+ 兼容导入
try:
    from fastmcp.server.auth.providers.jwt import RSAKeyPair
except ImportError:
    from fastmcp.server.auth.providers.bearer import RSAKeyPair


def generate_keys() -> RSAKeyPair:
    """生成 RSA 2048 位密钥对并保存到 keys/ 目录"""
    os.makedirs("keys", exist_ok=True)

    print("正在生成 RSA 2048 位密钥对...")
    key_pair = RSAKeyPair.generate()

    key_pair.save_private("keys/private.pem")
    key_pair.save_public("keys/public.pem")

    # 在类 Unix 系统上设置权限
    if os.name != "nt":
        os.chmod("keys/private.pem", 0o600)
        os.chmod("keys/public.pem", 0o644)

    print("密钥对已生成:")
    print("  私钥: keys/private.pem")
    print("  公钥: keys/public.pem")

    return key_pair


def create_token(key_pair: RSAKeyPair, expires_days: int = 365) -> str:
    """使用私钥签发 JWT Token"""
    token = key_pair.create_token(
        subject="mcp-client",
        issuer="leo-mcp-server",
        audience="mcp-clients",
        scopes=["tools:read", "tools:write", "resources:read"],
        expires_delta=timedelta(days=expires_days),
    )
    return token


def main() -> None:
    # 1. 生成密钥对
    key_pair = generate_keys()

    # 2. 签发 Token（默认有效期 365 天）
    token = create_token(key_pair)

    # 3. 生成客户端配置文件
    config = {
        "server_url": "http://YOUR_SERVER_IP:9100/sse",
        "transport": "sse",
        "headers": {"Authorization": f"Bearer {token}"},
        "token": token,
        "generated_at": datetime.now().isoformat(),
        "expires_in": "365天",
        "note": "将 server_url 中的 YOUR_SERVER_IP 替换为实际服务器 IP",
    }

    with open("client_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    # 4. 生成 .env 文件
    env_content = (
        "# FastMCP 服务器环境变量\n"
        "MCP_HOST=0.0.0.0\n"
        "MCP_PORT=9100\n"
        "MCP_ISSUER=leo-work-mcp-server\n"
        "MCP_AUDIENCE=mcp-clients\n"
        "MCP_PUBLIC_KEY_PATH=keys/public.pem\n"
        "MCP_BASE_DIR=/var/mcp/data\n"
    )

    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)

    print(f"\nJWT Token 已生成 (前50字符):")
    print(f"  {token[:50]}...")
    print(f"\n客户端配置已保存到: client_config.json")
    print(f"服务器环境变量已保存到: .env")
    print(f"\n下一步:")
    print(f"  1. 修改 client_config.json 中的 server_url，填入实际服务器 IP")
    print(f"  2. 启动服务器: python server.py")
    print(f"  3. 将 client_config.json 中的配置写入大模型客户端配置文件")


if __name__ == "__main__":
    main()
