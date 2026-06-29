FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py auth.py database.py models.py schemas.py stocks.json ./

# Sharia screener lives in the parent tools/ directory at build time;
# the Dockerfile context includes it via .dockerignore exception
COPY sharia_screener.py ./sharia_screener.py

ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
