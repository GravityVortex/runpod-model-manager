FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制脚本
COPY modelscope_patch.py .
COPY models_config.py .
COPY download_models.py .

CMD ["python", "download_models.py"]
