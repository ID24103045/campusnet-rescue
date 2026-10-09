# CNR-04 vulnerable portal. Pinned base; unprivileged user; no secrets baked in.
FROM python:3.12.5-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd -u 10001 -M -s /usr/sbin/nologin portal
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/app.py .
USER 10001
EXPOSE 8081
CMD ["gunicorn", "-b", "0.0.0.0:8081", "-w", "2", "--access-logfile", "-", "app:app"]
