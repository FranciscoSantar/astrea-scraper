FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN  playwright install chromium && \
    playwright install-deps chromium

COPY . .

CMD ["python3", "main.py"]
