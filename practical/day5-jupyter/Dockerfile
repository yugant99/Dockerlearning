FROM jupyter/scipy-notebook:latest

USER root

# Install system packages
RUN apt-get update && apt-get install -y \
    vim \
    && rm -rf /var/lib/apt/lists/*

USER jovyan

# Install Python packages
RUN pip install --no-cache-dir \
    pandas \
    scikit-learn \
    matplotlib \
    seaborn \
    plotly \
    google-cloud-bigquery \
    google-cloud-storage

# Set working directory
WORKDIR /home/jovyan/work
