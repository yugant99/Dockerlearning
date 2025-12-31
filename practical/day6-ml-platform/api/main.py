#!/usr/bin/env python3
"""
ML Model Serving API

FastAPI server that:
1. Loads trained model on startup
2. Serves predictions via REST API
3. Provides health and readiness endpoints

Endpoints:
    GET  /          - API info
    GET  /health    - Liveness probe
    GET  /ready     - Readiness probe (checks model loaded)
    POST /predict   - Make predictions
    GET  /metrics   - Basic metrics
"""

import os
import sys
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

import numpy as np
import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Configuration
MODEL_PATH = os.environ.get('MODEL_PATH', '/models/model.joblib')
MODEL_VERSION = os.environ.get('MODEL_VERSION', 'v1')

# Global state
model_artifact = None
model_loaded = False
prediction_count = 0
startup_time = None


# Request/Response models
class PredictionRequest(BaseModel):
    """Request body for prediction endpoint."""
    values: List[float] = Field(
        ..., 
        min_length=5,
        description="Last N values of time series (minimum 5)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "values": [100, 105, 103, 108, 110]
            }
        }


class PredictionResponse(BaseModel):
    """Response from prediction endpoint."""
    prediction: float
    model_version: str
    timestamp: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "prediction": 112.34,
                "model_version": "v1",
                "timestamp": "2024-12-30T10:00:00"
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str


class ReadyResponse(BaseModel):
    """Readiness check response."""
    status: str
    model_loaded: bool
    model_path: str
    model_version: str


class MetricsResponse(BaseModel):
    """Metrics response."""
    prediction_count: int
    uptime_seconds: float
    model_version: str
    model_metrics: Optional[dict]


# Lifespan handler (loads model on startup)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, cleanup on shutdown."""
    global model_artifact, model_loaded, startup_time
    
    startup_time = datetime.now()
    print(f"Starting ML API server...")
    print(f"Model path: {MODEL_PATH}")
    
    try:
        if os.path.exists(MODEL_PATH):
            print(f"Loading model from {MODEL_PATH}...")
            model_artifact = joblib.load(MODEL_PATH)
            model_loaded = True
            print(f"Model loaded successfully!")
            print(f"Model trained at: {model_artifact.get('trained_at', 'unknown')}")
            print(f"Model metrics: {model_artifact.get('metrics', {})}")
        else:
            print(f"WARNING: Model not found at {MODEL_PATH}")
            print("Server will start but predictions will fail until model is available")
    except Exception as e:
        print(f"ERROR loading model: {e}")
        model_loaded = False
    
    yield  # Server runs
    
    # Cleanup
    print("Shutting down ML API server...")


# Create FastAPI app
app = FastAPI(
    title="ML Prediction API",
    description="Time-series forecasting API running on Kubernetes",
    version=MODEL_VERSION,
    lifespan=lifespan
)


@app.get("/", response_model=dict)
async def root():
    """API information."""
    return {
        "name": "ML Prediction API",
        "version": MODEL_VERSION,
        "model_loaded": model_loaded,
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "predict": "/predict (POST)",
            "metrics": "/metrics"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Liveness probe endpoint.
    
    Returns 200 if the server process is alive.
    Used by Kubernetes liveness probe.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )


@app.get("/ready", response_model=ReadyResponse)
async def ready():
    """
    Readiness probe endpoint.
    
    Returns 200 only if model is loaded and ready to serve.
    Used by Kubernetes readiness probe.
    """
    if not model_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Service not ready."
        )
    
    return ReadyResponse(
        status="ready",
        model_loaded=model_loaded,
        model_path=MODEL_PATH,
        model_version=MODEL_VERSION
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Make a prediction using the trained model.
    
    Expects a list of recent values and predicts the next value.
    """
    global prediction_count
    
    if not model_loaded or model_artifact is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please try again later."
        )
    
    try:
        values = np.array(request.values)
        
        # Create features from the input values
        # We need: day_of_week, day_of_month, month, lag_1, lag_2, lag_3, lag_7, rolling_mean_7, rolling_std_7
        
        # For simplicity, we'll use current date for calendar features
        now = datetime.now()
        
        features = {
            'day_of_week': now.weekday(),
            'day_of_month': now.day,
            'month': now.month,
            'lag_1': values[-1] if len(values) >= 1 else 0,
            'lag_2': values[-2] if len(values) >= 2 else 0,
            'lag_3': values[-3] if len(values) >= 3 else 0,
            'lag_7': values[-7] if len(values) >= 7 else values[0],
            'rolling_mean_7': np.mean(values[-7:]) if len(values) >= 7 else np.mean(values),
            'rolling_std_7': np.std(values[-7:]) if len(values) >= 7 else np.std(values)
        }
        
        # Get feature order from model artifact
        feature_cols = model_artifact.get('feature_cols', list(features.keys()))
        
        # Create feature array in correct order
        X = np.array([[features[col] for col in feature_cols]])
        
        # Make prediction
        model = model_artifact['model']
        prediction = model.predict(X)[0]
        
        prediction_count += 1
        
        return PredictionResponse(
            prediction=round(float(prediction), 2),
            model_version=MODEL_VERSION,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@app.get("/metrics", response_model=MetricsResponse)
async def metrics():
    """
    Basic metrics endpoint.
    
    In production, you'd use Prometheus metrics instead.
    """
    uptime = (datetime.now() - startup_time).total_seconds() if startup_time else 0
    
    return MetricsResponse(
        prediction_count=prediction_count,
        uptime_seconds=round(uptime, 2),
        model_version=MODEL_VERSION,
        model_metrics=model_artifact.get('metrics') if model_artifact else None
    )


# Entry point for running directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

