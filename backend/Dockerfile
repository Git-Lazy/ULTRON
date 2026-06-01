FROM python:3.12.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu126
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
WORKDIR /app/api
CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000" ]