# MyCTF application image (dev build — Flask app, runnable as-is).
# The production API would swap to uvicorn/gunicorn + FastAPI; see ARCHITECTURE.md.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Non-root runtime user.
RUN useradd -m myctf && chown -R myctf:myctf /app
USER myctf

EXPOSE 8000
# Dev server. In production run behind gunicorn/uvicorn + a reverse proxy.
CMD ["python", "run.py"]
