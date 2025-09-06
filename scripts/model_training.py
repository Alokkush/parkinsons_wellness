#!/usr/bin/env python3
"""
🧠 Parkinson's Disease Prediction Model Training (Path Fixed)
============================================================
Advanced ML pipeline with correct path handling for Streamlit deployment.

Author: AI Wellness Team
Version: 2.1.0
"""

# Safe log utility to avoid errors if logging is not needed
def safe_log(msg, level="info"):
    try:
        if level == "info":
            logger.info(msg)
        elif level == "error":
            logger.error(msg)
        else:
            logger.debug(msg)
    except Exception:
        pass

import pandas as pd
import numpy as np
from sklearn.model_selection import (
    train_test_split, GridSearchCV, cross_val_score, 
    StratifiedKFold, learning_curve
)
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.svm import SVC
from sklearn.ensemble import (
    RandomForestClassifier, 
    GradientBoostingClassifier, 
    VotingClassifier
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, classification_report, 
    confusion_matrix, roc_auc_score, roc_curve,
    f1_score
)
import joblib
import os
from pathlib import Path
import warnings
from datetime import datetime
import json
import logging

# Optional imports with error handling
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_paths():
    """Setup all required paths for the project"""
    # Get the project root (parent of scripts directory)
    if Path.cwd().name == 'scripts':
        # We're running from scripts directory
        PROJECT_ROOT = Path.cwd().parent
    else:
        # We're running from project root
        PROJECT_ROOT = Path.cwd()
    
    paths = {
        'PROJECT_ROOT': PROJECT_ROOT,
        'DATA_PATH': PROJECT_ROOT / "data" / "parkinsons.csv",
        'MODELS_DIR': PROJECT_ROOT / "models",  # Main models directory
        'SCRIPTS_MODELS_DIR': PROJECT_ROOT / "scripts" / "models",  # Backup location
        'PLOTS_DIR': PROJECT_ROOT / "plots"
    }
    
    # Create all directories
    for dir_path in [paths['MODELS_DIR'], paths['SCRIPTS_MODELS_DIR'], paths['PLOTS_DIR']]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    return paths

class ParkinsonsModelTrainer:
    """Advanced model trainer with correct path handling"""
    
    def __init__(self):
        self.paths = setup_paths()
        self.models = {}
        self.results = {}
        self.best_model = None
        self.best_score = 0
        self.best_name = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.X = None
        self.y = None
        self.feature_names = None
        
        print("🔍 Path Configuration:")
        print(f"   📁 Project Root: {self.paths['PROJECT_ROOT']}")
        print(f"   📁 Data Path: {self.paths['DATA_PATH']}")
        print(f"   📁 Models Directory: {self.paths['MODELS_DIR']}")
        print(f"   📁 Plots Directory: {self.paths['PLOTS_DIR']}")
        
    def load_and_prepare_data(self):
        """Load and prepare the dataset"""
        safe_log("Loading and preparing dataset...", "info")
        if not self.paths['DATA_PATH'].exists():
            print("Dataset not found!")
            print("Please download the Parkinson's dataset from:")
            print("https://archive.ics.uci.edu/ml/datasets/parkinsons")
            print(f"Save as: {self.paths['DATA_PATH']}")
            raise FileNotFoundError("Dataset not found")

        # Load dataset
        df = pd.read_csv(self.paths['DATA_PATH'])
        safe_log(f"Dataset loaded: {df.shape}", "info")

        # Basic info
        print(f"\nDataset Overview:")
        print(f"   Shape: {df.shape}")
        print(f"   Features: {df.shape[1] - 1}")
        print(f"   Samples: {df.shape[0]}")

        # Handle name column if it exists
        if "name" in df.columns:
            df = df.drop(columns=["name"])
            safe_log("Removed 'name' column", "info")

        # Separate features and target
        X = df.drop(columns=["status"])
        y = df["status"]

        # Class distribution
        class_dist = y.value_counts()
        print(f"   Healthy: {class_dist[0]} ({class_dist[0]/len(y)*100:.1f}%)")
        print(f"   Parkinson's: {class_dist[1]} ({class_dist[1]/len(y)*100:.1f}%)")

        # Feature statistics
        print(f"\nFeature Analysis:")
        print(f"   Missing values: {X.isnull().sum().sum()}")
        print(f"   Numeric features: {len(X.select_dtypes(include=[np.number]).columns)}")
        print(f"   Feature range: [{X.min().min():.3f}, {X.max().max():.3f}]")

        # Store data
        self.X = X
        self.y = y
        self.feature_names = X.columns.tolist()

        return X, y
    
    def create_advanced_models(self):
        """Create ensemble of ML models"""
        logger.info("🔧 Creating model ensemble...")
        
        # Core models that should always work
        self.models = {
            "SVM_RBF": Pipeline([
                ("scaler", StandardScaler()),
                ("feature_selection", SelectKBest(f_classif, k=15)),
                ("clf", SVC(probability=True, random_state=42))
            ]),
            
            "RandomForest": Pipeline([
                ("scaler", StandardScaler()),
                ("clf", RandomForestClassifier(
                    n_estimators=100, 
                    max_depth=10,
                    random_state=42,
                    class_weight='balanced'
                ))
            ]),
            
            "GradientBoosting": Pipeline([
                ("scaler", StandardScaler()),
                ("clf", GradientBoostingClassifier(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=5,
                    random_state=42
                ))
            ]),
            
            "LogisticRegression": Pipeline([
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(
                    C=1.0,
                    max_iter=1000,
                    random_state=42,
                    class_weight='balanced'
                ))
            ])
        }
        
        # Add XGBoost if available
        if XGBOOST_AVAILABLE:
            self.models["XGBoost"] = Pipeline([
                ("scaler", StandardScaler()),
                ("clf", xgb.XGBClassifier(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=5,
                    random_state=42,
                    eval_metric='logloss',
                    use_label_encoder=False
                ))
            ])
            print("✅ XGBoost added to models")
        
        # Add LightGBM if available
        if LIGHTGBM_AVAILABLE:
            self.models["LightGBM"] = Pipeline([
                ("scaler", StandardScaler()),
                ("clf", lgb.LGBMClassifier(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=5,
                    random_state=42,
                    verbose=-1
                ))
            ])
            print("✅ LightGBM added to models")
        
        print(f"✅ Created {len(self.models)} models")
    
    def train_and_evaluate(self):
        """Train all models with basic hyperparameter optimization"""
        logger.info("🚀 Starting model training...")
        
        # Split data
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42, stratify=self.y
        )
        
        print(f"\n📊 Data Split:")
        print(f"   • Training: {self.X_train.shape[0]} samples")
        print(f"   • Testing: {self.X_test.shape[0]} samples")
        
        cv_folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        
        print(f"\n🔄 Training Models:")
        print("=" * 60)
        
        for name, pipeline in self.models.items():
            print(f"\n🎯 Training {name}...")
            
            try:
                # Simple training without extensive grid search for reliability
                pipeline.fit(self.X_train, self.y_train)
                
                # Cross-validation score
                cv_scores = cross_val_score(pipeline, self.X_train, self.y_train, 
                                          cv=cv_folds, scoring='accuracy')
                cv_mean = cv_scores.mean()
                cv_std = cv_scores.std()
                
                # Test set evaluation
                y_pred = pipeline.predict(self.X_test)
                y_proba = pipeline.predict_proba(self.X_test)[:, 1]
                
                test_accuracy = accuracy_score(self.y_test, y_pred)
                test_f1 = f1_score(self.y_test, y_pred)
                test_auc = roc_auc_score(self.y_test, y_proba)
                
                # Store results
                self.results[name] = {
                    'best_estimator': pipeline,
                    'cv_score': cv_mean,
                    'cv_std': cv_std,
                    'test_accuracy': test_accuracy,
                    'test_f1': test_f1,
                    'test_auc': test_auc,
                    'predictions': y_pred,
                    'probabilities': y_proba
                }
                
                print(f"   ✅ CV Score: {cv_mean:.4f} (±{cv_std:.4f})")
                print(f"   ✅ Test Accuracy: {test_accuracy:.4f}")
                print(f"   ✅ Test F1: {test_f1:.4f}")
                print(f"   ✅ Test AUC: {test_auc:.4f}")
                
                # Update best model
                if cv_mean > self.best_score:
                    self.best_score = cv_mean
                    self.best_model = pipeline
                    self.best_name = name
                    
            except Exception as e:
                logger.error(f"❌ Error training {name}: {e}")
                print(f"   ❌ Training failed: {e}")
                continue
        
        print("\n" + "=" * 60)
        if self.best_name:
            print(f"🏆 Best Model: {self.best_name}")
            print(f"🎯 Best CV Score: {self.best_score:.4f}")
        else:
            print("❌ No successful model training!")
        print("=" * 60)
    
    def save_model_and_results(self):
        """Save the best model and results to multiple locations"""
        logger.info("💾 Saving model and results...")
        
        if not self.best_model:
            logger.error("❌ No model to save!")
            return
        
        # Save to main models directory (for Streamlit app)
        main_model_path = self.paths['MODELS_DIR'] / "parkinsons_model.pkl"
        joblib.dump(self.best_model, main_model_path)
        print(f"✅ Model saved to: {main_model_path}")
        
        # Save to scripts/models directory (backup)
        backup_model_path = self.paths['SCRIPTS_MODELS_DIR'] / "parkinsons_model.pkl"
        joblib.dump(self.best_model, backup_model_path)
        print(f"✅ Backup saved to: {backup_model_path}")
        
        # Save feature names
        feature_paths = [
            self.paths['MODELS_DIR'] / "feature_names.pkl",
            self.paths['SCRIPTS_MODELS_DIR'] / "feature_names.pkl"
        ]
        for feature_path in feature_paths:
            joblib.dump(self.feature_names, feature_path)
        
        # Save scaler if it exists in the pipeline
        if isinstance(self.best_model, Pipeline) and 'scaler' in self.best_model.named_steps:
            scaler = self.best_model.named_steps['scaler']
            scaler_paths = [
                self.paths['MODELS_DIR'] / "scaler.pkl",
                self.paths['SCRIPTS_MODELS_DIR'] / "scaler.pkl"
            ]
            for scaler_path in scaler_paths:
                joblib.dump(scaler, scaler_path)
        
        # Save comprehensive results
        results_summary = {
            'training_date': datetime.now().isoformat(),
            'best_model': self.best_name,
            'best_cv_score': float(self.best_score),
            'dataset_info': {
                'total_samples': len(self.X) if self.X is not None else 0,
                'features': len(self.X.columns) if self.X is not None else 0,
                'feature_names': self.feature_names if self.feature_names is not None else [],
                'class_distribution': self.y.value_counts().to_dict() if self.y is not None else {}
            },
            'model_performance': {}
        }
        
        for name, result in self.results.items():
            results_summary['model_performance'][name] = {
                'cv_score': float(result['cv_score']),
                'test_accuracy': float(result['test_accuracy']),
                'test_f1': float(result['test_f1']),
                'test_auc': float(result['test_auc'])
            }
        
        # Save results to both locations
        result_paths = [
            self.paths['MODELS_DIR'] / "training_results.json",
            self.paths['SCRIPTS_MODELS_DIR'] / "training_results.json"
        ]
        for result_path in result_paths:
            with open(result_path, 'w') as f:
                json.dump(results_summary, f, indent=2)
        
        print(f"✅ Results saved to: {self.paths['MODELS_DIR']}/training_results.json")
        
        # Generate classification report
        if self.y_test is not None and 'predictions' in self.results[self.best_name]:
            best_predictions = self.results[self.best_name]['predictions']
            report = classification_report(self.y_test, best_predictions, output_dict=True)
            
            report_paths = [
                self.paths['MODELS_DIR'] / "classification_report.json",
                self.paths['SCRIPTS_MODELS_DIR'] / "classification_report.json"
            ]
            for report_path in report_paths:
                with open(report_path, 'w') as f:
                    json.dump(report, f, indent=2)
    
    def create_basic_visualization(self):
        """Create basic model comparison if matplotlib is available"""
        if not PLOTTING_AVAILABLE:
            print("⚠️ Matplotlib not available, skipping plots")
            return
            
        try:
            logger.info("📊 Creating basic visualization...")
            
            # Simple bar chart of model performance
            fig, ax = plt.subplots(1, 1, figsize=(10, 6))
            
            models = list(self.results.keys())
            scores = [self.results[m]['cv_score'] for m in models]
            
            bars = ax.bar(models, scores, color='skyblue', alpha=0.7)
            ax.set_title('🎯 Model Comparison (CV Scores)', fontsize=14, fontweight='bold')
            ax.set_ylabel('Accuracy Score')
            ax.tick_params(axis='x', rotation=45)
            ax.set_ylim((0.8, 1.0))
            
            # Add value labels
            for bar, score in zip(bars, scores):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.005,
                       f'{score:.3f}', ha='center', va='bottom', fontweight='bold')
            
            plt.tight_layout()
            
            # Save to both locations
            plot_paths = [
                self.paths['PLOTS_DIR'] / 'model_comparison.png',
                self.paths['SCRIPTS_MODELS_DIR'] / 'model_comparison.png'
            ]
            for plot_path in plot_paths:
                plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            
            plt.close()
            print(f"✅ Basic visualization saved")
            
        except Exception as e:
            print(f"⚠️ Visualization failed: {e}")
    
    def print_final_summary(self):
        """Print comprehensive training summary"""
        print("\n" + "="*80)
        print("🧠 PARKINSON'S DISEASE PREDICTION MODEL - TRAINING COMPLETE")
        print("="*80)
        
        if self.best_name:
            print(f"🏆 Best Model: {self.best_name}")
            print(f"🎯 Cross-validation Score: {self.best_score:.4f}")
            print(f"🎯 Test Accuracy: {self.results[self.best_name]['test_accuracy']:.4f}")
            print(f"🎯 Test F1 Score: {self.results[self.best_name]['test_f1']:.4f}")
            print(f"🎯 Test AUC Score: {self.results[self.best_name]['test_auc']:.4f}")
        else:
            print("❌ No successful model training completed!")
            return
        
        print(f"\n📊 Dataset: {len(self.X) if self.X is not None else 0} samples, {len(self.X.columns) if self.X is not None else 0} features")
        print(f"🔍 Main models directory: {self.paths['MODELS_DIR']}")
        print(f"🔍 Backup models directory: {self.paths['SCRIPTS_MODELS_DIR']}")

        # Verify model files exist
        main_model_path = self.paths['MODELS_DIR'] / "parkinsons_model.pkl"
        if main_model_path.exists():
            print(f"✅ Model ready for Streamlit app: {main_model_path}")
        else:
            print(f"❌ Model file missing: {main_model_path}")

        print(f"\n🚀 Ready to run Streamlit app:")
        print(f"   cd {self.paths['PROJECT_ROOT']}")
        print(f"   streamlit run app/main.py")

        print("="*80)


def main():
    """Main training pipeline"""
    print("🧠 Parkinson's Disease Prediction Model Training")
    print("=" * 50)
    print("🚀 Starting ML pipeline...")
    
    trainer = ParkinsonsModelTrainer()
    
    try:
        # Load and prepare data
        trainer.load_and_prepare_data()
        
        # Create models
        trainer.create_advanced_models()
        
        # Train and evaluate
        trainer.train_and_evaluate()
        
        # Create basic visualization
        trainer.create_basic_visualization()
        
        # Save everything
        trainer.save_model_and_results()
        
        # Print summary
        trainer.print_final_summary()
        
        logger.info("✅ Training pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Training pipeline failed: {e}")
        print(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()