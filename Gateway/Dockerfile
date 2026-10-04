FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    --trusted-host mirrors.aliyun.com \
    -i http://pypi.tuna.tsinghua.edu.cn/simple/ \
    -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]