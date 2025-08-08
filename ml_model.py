"""Machine Learning model for price prediction"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
import logging
from config import ML_FEATURES

logger = logging.getLogger(__name__)

class MLPredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for ML model
        
        Args:
            df: DataFrame with technical indicators
            
        Returns:
            DataFrame with ML features
        """
        df = df.copy()
        
        # Create target variable (next day price movement)
        df['Next_Day_Return'] = df['Close'].shift(-1) / df['Close'] - 1
        df['Target'] = (df['Next_Day_Return'] > 0).astype(int)
        
        # Select features that exist in the dataframe
        available_features = [col for col in ML_FEATURES if col in df.columns]
        self.feature_columns = available_features
        
        # Handle missing values
        df = df.dropna()
        
        return df
    
    def train_model(self, df: pd.DataFrame, model_type: str = 'random_forest') -> dict:
        """
        Train ML model
        
        Args:
            df: DataFrame with features and target
            model_type: Type of model to use ('random_forest' or 'logistic_regression')
            
        Returns:
            Dictionary with training results
        """
        if len(self.feature_columns) == 0:
            logger.error("No valid features found for training")
            return {}
        
        # Prepare features and target
        X = df[self.feature_columns].fillna(0)
        y = df['Target']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        if model_type == 'random_forest':
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        else:
            self.model = LogisticRegression(random_state=42, max_iter=1000)
        
        self.model.fit(X_train_scaled, y_train)
        
        # Make predictions
        y_pred = self.model.predict(X_test_scaled)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        
        results = {
            'Model_Type': model_type,
            'Accuracy': accuracy,
            'Features_Used': self.feature_columns,
            'Training_Samples': len(X_train),
            'Test_Samples': len(X_test)
        }
        
        logger.info(f"Model trained with accuracy: {accuracy:.4f}")
        return results
    
    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Make predictions on new data
        
        Args:
            df: DataFrame with features
            
        Returns:
            Array of predictions
        """
        if self.model is None:
            logger.error("Model not trained yet")
            return np.array([])
        
        X = df[self.feature_columns].fillna(0)
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        return predictions
