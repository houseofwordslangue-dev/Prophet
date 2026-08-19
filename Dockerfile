FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PM_HOST=0.0.0.0 PM_PORT=8080
WORKDIR /app
RUN groupadd --system app && useradd --system --gid app --home /app app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/data /app/backups && chown -R app:app /app/data /app/backups
USER app
EXPOSE 8080
VOLUME ["/app/data","/app/backups"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/ready',timeout=3).read()" || exit 1
CMD ["python","server.py"]
