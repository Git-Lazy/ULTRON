FROM python:3.12.9-slim
WORKDIR /app
RUN pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu126
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000" ]