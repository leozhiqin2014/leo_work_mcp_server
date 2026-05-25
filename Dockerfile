FROM python:3.11-slim

WORKDIR /app

# 安装系统工具（ping 依赖 iputils-ping）
RUN apt-get update && apt-get install -y \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://mirrors.tencent.com/pypi/simple/ -r requirements.txt

# 创建非 root 用户和数据目录
RUN useradd -m -u 1000 mcpuser && \
    mkdir -p /var/mcp/data && \
    chown -R mcpuser:mcpuser /app /var/mcp/data

# 复制应用代码
COPY server.py .

# 复制工具模块
COPY tools/ tools/

# 复制 DAO 层
COPY dao/ dao/

# 复制 models 层
COPY models/ models/

# 复制 utils 层
COPY utils/ utils/

# 复制预生成的密钥对（如果存在）
RUN mkdir -p keys/
COPY keys/ keys/
RUN chown -R mcpuser:mcpuser keys/ 2>/dev/null || true

# 切换到非 root 用户运行
USER mcpuser

EXPOSE 9001

CMD ["python", "server.py"]
