# ML Training Container
# Builds a lightweight container for model training

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies first (for layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy training script
COPY train.py .

# Create models directory (will be overwritten by PVC mount)
RUN mkdir -p /models

# Default environment variables (can be overridden)
ENV MODEL_PATH=/models/model.joblib
ENV N_ESTIMATORS=100
ENV MAX_DEPTH=10
ENV N_SAMPLES=1000

# Run training
CMD ["python", "train.py"]

