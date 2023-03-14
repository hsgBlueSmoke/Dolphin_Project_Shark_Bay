FROM apache/airflow:2.5.1
USER root
RUN apt-get update \
  && apt-get install -y \
         libglib2.0-0 libgl1 \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
USER airflow
RUN pip install --no-cache-dir minio Pillow split-folders opencv-python airflow-code-editor
