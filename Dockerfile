FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目文件
COPY modelscope_patch.py .
COPY download_models.py .
COPY downloaders/ ./downloaders/
COPY projects/ ./projects/

# 默认执行下载所有项目的模型
CMD ["python", "download_models.py", "--all"]
