FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY stocks.json .

# Expose port (Render/Railway set PORT env var)
ENV PORT=8000
EXPOSE 8000

# Run with uvicorn
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT}
