# ML API Serving Container
# FastAPI server for model inference

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies first (for layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy API code
COPY main.py .

# Create models directory (will be overwritten by PVC mount)
RUN mkdir -p /models

# Default environment variables
ENV MODEL_PATH=/models/model.joblib
ENV MODEL_VERSION=v1

# Expose port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

