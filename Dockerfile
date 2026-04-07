# HuggingFace Spaces compatible Dockerfile — port 7860 required
# Using AWS Public ECR mirror to bypass Docker Hub rate limiting on the Hackathon validator
FROM public.ecr.aws/docker/library/python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN useradd -m -u 1000 appuser

WORKDIR /app

COPY server/requirements.txt /app/server/
RUN pip install --no-cache-dir -r /app/server/requirements.txt

COPY server/ /app/server/
COPY openenv.yaml /app/

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 7860

HEALTHCHECK --interval=30s CMD curl -f http://localhost:7860/health || exit 1

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "7860"]
