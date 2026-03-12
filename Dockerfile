# 基础镜像：Ubuntu 22.04 LTS 精简版
FROM ac2-registry.cn-hangzhou.cr.aliyuncs.com/ac2/base:ubuntu22.04

# 配置镜像源（加速apt安装，可选）
RUN echo "deb http://mirrors.aliyun.com/ubuntu/ jammy main restricted universe multiverse" > /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/ubuntu/ jammy-updates main restricted universe multiverse" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/ubuntu/ jammy-security main restricted universe multiverse" >> /etc/apt/sources.list

# 安装必要工具（按需增减，保证功能完整）
RUN apt update && \
    apt install -y --no-install-recommends \
    iputils-ping \    
    curl \            
    sudo \            
    vim-tiny \        
    procps \          
    net-tools \       
    && apt clean && \ 
    rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /home/openclaw

# 示例：添加普通用户（可选，符合安全规范）
RUN useradd -m openclaw && echo "openclaw ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
USER openclaw

# 容器启动命令（按需修改）
CMD ["sleep", "infinity"]