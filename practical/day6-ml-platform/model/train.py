#!/usr/bin/env python3
"""
ML Training Script - Time Series Forecasting

This script:
1. Generates synthetic time-series data (or loads from file)
2. Creates lag features for forecasting
3. Trains a RandomForestRegressor
4. Saves the model to the specified path
5. Prints evaluation metrics

Environment Variables:
    MODEL_PATH: Where to save the model (default: /models/model.joblib)
    N_ESTIMATORS: Number of trees (default: 100)
    MAX_DEPTH: Max tree depth (default: 10)
    N_SAMPLES: Number of training samples (default: 1000)
"""

import os
import sys
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
from datetime import datetime

# Configuration from environment
MODEL_PATH = os.environ.get('MODEL_PATH', '/models/model.joblib')
N_ESTIMATORS = int(os.environ.get('N_ESTIMATORS', '100'))
MAX_DEPTH = int(os.environ.get('MAX_DEPTH', '10'))
N_SAMPLES = int(os.environ.get('N_SAMPLES', '1000'))


def generate_time_series_data(n_samples: int = 1000) -> pd.DataFrame:
    """
    Generate synthetic time-series data with trend, seasonality, and noise.
    
    Simulates daily demand data (like what you'd see at BigBasket).
    """
    np.random.seed(42)
    
    # Create date range
    dates = pd.date_range(start='2023-01-01', periods=n_samples, freq='D')
    
    # Base trend (slight upward)
    trend = np.linspace(100, 150, n_samples)
    
    # Weekly seasonality (higher on weekends)
    day_of_week = np.array([d.dayofweek for d in dates])
    weekly_pattern = np.where(day_of_week >= 5, 20, 0)  # Weekend boost
    
    # Monthly seasonality
    day_of_month = np.array([d.day for d in dates])
    monthly_pattern = 10 * np.sin(2 * np.pi * day_of_month / 30)
    
    # Random noise
    noise = np.random.normal(0, 10, n_samples)
    
    # Combine components
    values = trend + weekly_pattern + monthly_pattern + noise
    
    df = pd.DataFrame({
        'date': dates,
        'value': values,
        'day_of_week': day_of_week,
        'day_of_month': day_of_month,
        'month': [d.month for d in dates]
    })
    
    return df


def create_lag_features(df: pd.DataFrame, lags: list = [1, 2, 3, 7]) -> pd.DataFrame:
    """
    Create lag features for time-series forecasting.
    
    Args:
        df: DataFrame with 'value' column
        lags: List of lag periods to create
    
    Returns:
        DataFrame with lag features added
    """
    df = df.copy()
    
    for lag in lags:
        df[f'lag_{lag}'] = df['value'].shift(lag)
    
    # Rolling statistics
    df['rolling_mean_7'] = df['value'].shift(1).rolling(7).mean()
    df['rolling_std_7'] = df['value'].shift(1).rolling(7).std()
    
    # Drop rows with NaN (from lagging)
    df = df.dropna()
    
    return df


def train_model(X_train, y_train) -> RandomForestRegressor:
    """Train the forecasting model."""
    
    model = RandomForestRegressor(
        n_estimators=N_ESTIMATORS,
        max_depth=MAX_DEPTH,
        random_state=42,
        n_jobs=-1  # Use all cores
    )
    
    model.fit(X_train, y_train)
    return model


def evaluate_model(model, X_test, y_test) -> dict:
    """Evaluate model and return metrics."""
    
    predictions = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    
    return {
        'mae': mae,
        'rmse': rmse
    }


def main():
    print("=" * 50)
    print("ML Training Pipeline")
    print("=" * 50)
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"Model path: {MODEL_PATH}")
    print(f"N_ESTIMATORS: {N_ESTIMATORS}")
    print(f"MAX_DEPTH: {MAX_DEPTH}")
    print(f"N_SAMPLES: {N_SAMPLES}")
    print("=" * 50)
    
    # Step 1: Generate data
    print("\n[1/5] Generating time-series data...")
    df = generate_time_series_data(N_SAMPLES)
    print(f"Generated {len(df)} samples")
    
    # Step 2: Feature engineering
    print("\n[2/5] Creating features...")
    df = create_lag_features(df)
    print(f"Features created, {len(df)} samples after dropping NaN")
    
    # Step 3: Prepare training data
    print("\n[3/5] Preparing train/test split...")
    feature_cols = ['day_of_week', 'day_of_month', 'month', 
                    'lag_1', 'lag_2', 'lag_3', 'lag_7',
                    'rolling_mean_7', 'rolling_std_7']
    
    X = df[feature_cols]
    y = df['value']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False  # Time series: no shuffle!
    )
    print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
    
    # Step 4: Train model
    print("\n[4/5] Training RandomForestRegressor...")
    model = train_model(X_train, y_train)
    print("Training complete!")
    
    # Step 5: Evaluate
    print("\n[5/5] Evaluating model...")
    metrics = evaluate_model(model, X_test, y_test)
    print(f"MAE:  {metrics['mae']:.4f}")
    print(f"RMSE: {metrics['rmse']:.4f}")
    
    # Save model
    print(f"\nSaving model to {MODEL_PATH}...")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    
    # Save with metadata
    model_artifact = {
        'model': model,
        'feature_cols': feature_cols,
        'metrics': metrics,
        'trained_at': datetime.now().isoformat(),
        'config': {
            'n_estimators': N_ESTIMATORS,
            'max_depth': MAX_DEPTH,
            'n_samples': N_SAMPLES
        }
    }
    
    joblib.dump(model_artifact, MODEL_PATH)
    print(f"Model saved successfully!")
    
    # Verify save
    file_size = os.path.getsize(MODEL_PATH)
    print(f"File size: {file_size / 1024:.2f} KB")
    
    print("\n" + "=" * 50)
    print("Training complete!")
    print("=" * 50)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

