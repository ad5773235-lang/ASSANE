FROM python:3.11-slim

WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium
COPY backend ./backend
COPY .env.example ./.env.example

ENV PYTHONPATH=/app/backend
EXPOSE 8000
CMD ["python", "backend/run.py"]
