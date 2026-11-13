FROM python:3.14-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jre-headless libgomp1 procps git build-essential && rm -rf /var/lib/apt/lists/*
WORKDIR /artifact
COPY requirements.lock pyproject.toml README.md /artifact/
RUN pip install --no-cache-dir -r requirements.lock
COPY . /artifact
RUN pip install --no-cache-dir --no-deps -e .
ENV SPARK_LOCAL_IP=127.0.0.1
CMD ["python", "tools/verify_artifact.py"]

