FROM python:3.9-slim

# Install the latest OpenAI library (>=0.27.0)
RUN pip install --upgrade pip && \
    pip install pymysql configparser flask==3.0.2 gradio && \
    pip install --no-cache-dir --upgrade openai && \
    pip install langchain-community pymysql sqlalchemy langchain_openai && \
    pip install paddlepaddle==3.0.0 -f https://www.paddlepaddle.org.cn/whl/macos/mkl/avx/stable.html && \
    pip install paddleocr && \
    apt-get update && apt-get install -y libgomp1 libgl1 libglib2.0-0 libsm6 libxext6

CMD ["python3"]

