"""
FastMCP HTTP+SSE 服务器 (3.x 版本)
运行模式: HTTP 服务，通过 Server-Sent Events 提供 MCP 服务
认证方式: Bearer JWT Token / OAuth 2.1
"""

import os
import logging
from typing import Optional

from fastmcp import FastMCP

# FastMCP 3.x auth imports
try:
    from fastmcp.server.auth.providers.jwt import JWTVerifier
except ImportError:
    JWTVerifier = None

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 从环境变量读取配置
SERVER_HOST = os.getenv("MCP_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("MCP_PORT", "9001"))


def load_public_key() -> tuple[Optional[str], Optional[str]]:
    """从文件或环境变量加载 RSA 公钥，返回 (key_content, key_source)"""
    # 优先从文件路径加载（默认 keys/public.pem）
    key_path = os.getenv("MCP_PUBLIC_KEY_PATH", "keys/public.pem")
    if os.path.isfile(key_path):
        with open(key_path, "r", encoding="utf-8") as f:
            return f.read(), key_path

    # 其次从环境变量直接读取
    key_content = os.getenv("MCP_PUBLIC_KEY")
    if key_content:
        return key_content, "环境变量 MCP_PUBLIC_KEY"

    return None, None


def create_mcp_server() -> FastMCP:
    """创建并配置 MCP 服务器实例"""
    # 从环境变量读取 JWT 配置
    jwt_enabled = os.getenv("MCP_JWT_ENABLED", "true").lower() == "true"
    jwt_issuer = os.getenv("MCP_ISSUER", "leo-work-mcp-server")
    jwt_audience = os.getenv("MCP_AUDIENCE", "mcp-clients")

    auth = None
    if jwt_enabled and JWTVerifier:
        public_key, key_source = load_public_key()

        if public_key:
            # 使用预生成的公钥
            auth = JWTVerifier(
                public_key=public_key,
                issuer=jwt_issuer,
                audience=jwt_audience,
            )
            logger.info(f"JWT 鉴权已启用（来源: {key_source}）")
            logger.info(f"  Issuer: {jwt_issuer}")
            logger.info(f"  Audience: {jwt_audience}")
        else:
            # 未找到密钥文件，禁用鉴权
            logger.warning("未找到公钥文件，JWT 鉴权已禁用")
            logger.warning("提示: 使用 generate_keys.py 生成密钥对并放入 keys/ 目录")
    else:
        if jwt_enabled:
            logger.warning("JWTVerifier 不可用，鉴权已禁用")
        else:
            logger.warning("JWT 鉴权已禁用（不推荐用于生产环境）")

    # 创建 MCP 服务器 - FastMCP 3.x 方式
    mcp = FastMCP(
        "Leo MCP Server",
        auth=auth,
    )

    return mcp


def register_tools(mcp: FastMCP) -> None:
    """注册工具和资源"""
    # 注册成员上下文工具
    from tools.member_context import register_tools as register_member_context_tools
    register_member_context_tools(mcp)

    @mcp.tool()
    def calculate(expression: str):
        """安全地计算数学表达式，支持 +、-、*、/、** 运算"""
        import ast
        import operator

        safe_ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }

        def _eval(node):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return node.value
            if isinstance(node, ast.Num):
                return node.n
            if isinstance(node, ast.BinOp):
                op_type = type(node.op)
                if op_type not in safe_ops:
                    raise ValueError(f"不支持的运算符: {node.op}")
                return safe_ops[op_type](_eval(node.left), _eval(node.right))
            if isinstance(node, ast.UnaryOp):
                op_type = type(node.op)
                if op_type not in safe_ops:
                    raise ValueError(f"不支持的运算符: {node.op}")
                return safe_ops[op_type](_eval(node.operand))
            raise ValueError(f"不支持的表达式类型: {type(node).__name__}")

        tree = ast.parse(expression, mode="eval")
        result = _eval(tree.body)
        return {"expression": expression, "result": result, "type": type(result).__name__}

    @mcp.tool()
    def list_tools():
        """列出服务器上所有可用的 MCP 工具"""
        tools_info = []
        try:
            tools = mcp._tools
            for name, tool in tools.items():
                tools_info.append({
                    "name": name,
                    "description": tool.description if hasattr(tool, "description") else "",
                })
        except:
            tools_info = [{"name": "calculate"}, {"name": "list_tools"}]
        return tools_info


def main():
    """主函数 - FastMCP 3.x 使用 run 方法"""
    mcp = create_mcp_server()
    register_tools(mcp)

    logger.info(f"服务器启动: {SERVER_HOST}:{SERVER_PORT}")
    logger.info("传输协议: http (FastMCP 3.x)")

    # FastMCP 3.x 使用 run 方法，transport="http"
    mcp.run(
        transport="http",
        host=SERVER_HOST,
        port=SERVER_PORT,
    )


if __name__ == "__main__":
    main()
