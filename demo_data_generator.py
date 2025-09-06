#!/usr/bin/env python3
"""
Demo Data Generator for Parkinson's Disease Prediction Testing
============================================================
Creates realistic synthetic test data based on the original dataset structure.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def create_demo_data():
    """Create realistic demo data for testing"""
    
    # Set random seed for reproducible results
    np.random.seed(42)
    
    # Original dataset features (based on the Parkinson's dataset)
    features = [
        'MDVP:Fo(Hz)', 'MDVP:Fhi(Hz)', 'MDVP:Flo(Hz)', 'MDVP:Jitter(%)',
        'MDVP:Jitter(Abs)', 'MDVP:RAP', 'MDVP:PPQ', 'Jitter:DDP',
        'MDVP:Shimmer', 'MDVP:Shimmer(dB)', 'Shimmer:APQ3', 'Shimmer:APQ5',
        'MDVP:APQ', 'Shimmer:DDA', 'NHR', 'HNR', 'RPDE', 'DFA',
        'spread1', 'spread2', 'D2', 'PPE'
    ]
    
    # Healthy person characteristics (lower jitter, shimmer, etc.)
    healthy_ranges = {
        'MDVP:Fo(Hz)': (120, 220),
        'MDVP:Fhi(Hz)': (140, 280),
        'MDVP:Flo(Hz)': (80, 180),
        'MDVP:Jitter(%)': (0.003, 0.008),
        'MDVP:Jitter(Abs)': (0.00001, 0.00005),
        'MDVP:RAP': (0.001, 0.005),
        'MDVP:PPQ': (0.001, 0.005),
        'Jitter:DDP': (0.003, 0.015),
        'MDVP:Shimmer': (0.01, 0.04),
        'MDVP:Shimmer(dB)': (0.08, 0.35),
        'Shimmer:APQ3': (0.005, 0.020),
        'Shimmer:APQ5': (0.006, 0.025),
        'MDVP:APQ': (0.008, 0.030),
        'Shimmer:DDA': (0.015, 0.060),
        'NHR': (0.001, 0.020),
        'HNR': (20, 30),
        'RPDE': (0.35, 0.55),
        'DFA': (0.55, 0.75),
        'spread1': (-6, -4),
        'spread2': (0.1, 0.3),
        'D2': (1.5, 2.5),
        'PPE': (0.05, 0.20)
    }
    
    # Parkinson's characteristics (higher jitter, shimmer, etc.)
    parkinsons_ranges = {
        'MDVP:Fo(Hz)': (90, 250),
        'MDVP:Fhi(Hz)': (110, 350),
        'MDVP:Flo(Hz)': (65, 200),
        'MDVP:Jitter(%)': (0.005, 0.030),
        'MDVP:Jitter(Abs)': (0.00002, 0.0002),
        'MDVP:RAP': (0.002, 0.018),
        'MDVP:PPQ': (0.002, 0.018),
        'Jitter:DDP': (0.006, 0.055),
        'MDVP:Shimmer': (0.02, 0.12),
        'MDVP:Shimmer(dB)': (0.15, 1.10),
        'Shimmer:APQ3': (0.010, 0.065),
        'Shimmer:APQ5': (0.012, 0.070),
        'MDVP:APQ': (0.015, 0.085),
        'Shimmer:DDA': (0.030, 0.195),
        'NHR': (0.005, 0.065),
        'HNR': (8, 25),
        'RPDE': (0.40, 0.70),
        'DFA': (0.50, 0.85),
        'spread1': (-8, -3),
        'spread2': (0.05, 0.45),
        'D2': (1.2, 3.2),
        'PPE': (0.08, 0.40)
    }
    
    def generate_sample(condition, patient_id):
        """Generate a single sample"""
        ranges = healthy_ranges if condition == 0 else parkinsons_ranges
        
        sample = {'name': f'patient_{patient_id:03d}'}
        
        for feature in features:
            min_val, max_val = ranges[feature]
            # Add some realistic noise
            value = np.random.uniform(min_val, max_val)
            sample[feature] = round(value, 6)
        
        sample['status'] = str(condition)
        return sample
    
    # Generate demo datasets
    datasets = {}
    
    # 1. Small mixed demo (10 samples)
    small_demo = []
    for i in range(5):  # 5 healthy
        small_demo.append(generate_sample(0, i))
    for i in range(5, 10):  # 5 Parkinson's
        small_demo.append(generate_sample(1, i))
    datasets['demo_small'] = pd.DataFrame(small_demo)
    
    # 2. Larger demo (50 samples)
    large_demo = []
    for i in range(20):  # 20 healthy
        large_demo.append(generate_sample(0, i))
    for i in range(20, 50):  # 30 Parkinson's
        large_demo.append(generate_sample(1, i))
    datasets['demo_large'] = pd.DataFrame(large_demo)
    
    # 3. Healthy only demo (20 samples)
    healthy_demo = []
    for i in range(20):
        healthy_demo.append(generate_sample(0, i))
    datasets['demo_healthy_only'] = pd.DataFrame(healthy_demo)
    
    # 4. Parkinson's only demo (20 samples)
    parkinsons_demo = []
    for i in range(20):
        parkinsons_demo.append(generate_sample(1, i))
    datasets['demo_parkinsons_only'] = pd.DataFrame(parkinsons_demo)
    
    # 5. Edge cases demo (samples near decision boundary)
    edge_demo = []
    for i in range(10):
        # Create samples with mixed characteristics
        sample = {'name': f'edge_patient_{i:03d}'}
        condition = np.random.choice([0, 1])
        
        for feature in features:
            # Mix characteristics from both conditions
            healthy_min, healthy_max = healthy_ranges[feature]
            parkinsons_min, parkinsons_max = parkinsons_ranges[feature]
            
            # Create overlap region
            overall_min = max(healthy_min, parkinsons_min)
            overall_max = min(healthy_max, parkinsons_max)
            
            if overall_min < overall_max:
                value = np.random.uniform(overall_min, overall_max)
            else:
                # No overlap, use mixed approach
                if np.random.random() < 0.5:
                    value = np.random.uniform(healthy_min, healthy_max)
                else:
                    value = np.random.uniform(parkinsons_min, parkinsons_max)
            
            sample[feature] = round(value, 6)
        
        sample['status'] = condition
        edge_demo.append(sample)
    
    datasets['demo_edge_cases'] = pd.DataFrame(edge_demo)
    
    return datasets

def save_demo_data():
    """Generate and save demo datasets"""
    print("Generating demo datasets...")
    
    # Create demo data directory
    demo_dir = Path("demo_data")
    demo_dir.mkdir(exist_ok=True)
    
    # Generate datasets
    datasets = create_demo_data()
    
    # Save each dataset
    for name, df in datasets.items():
        filepath = demo_dir / f"{name}.csv"
        df.to_csv(filepath, index=False)
        
        # Print dataset info
        class_dist = df['status'].value_counts()
        healthy_count = class_dist.get(0, 0)
        parkinsons_count = class_dist.get(1, 0)
        
        print(f"\n{name}.csv created:")
        print(f"  - Total samples: {len(df)}")
        print(f"  - Healthy: {healthy_count}")
        print(f"  - Parkinson's: {parkinsons_count}")
        print(f"  - Features: {len(df.columns) - 2}")  # Exclude name and status
        print(f"  - Saved to: {filepath}")
    
    # Create a summary file
    summary = {
        "demo_small.csv": "Small mixed dataset (10 samples) - good for quick testing",
        "demo_large.csv": "Larger mixed dataset (50 samples) - better for evaluation",
        "demo_healthy_only.csv": "Only healthy samples (20 samples) - test specificity",
        "demo_parkinsons_only.csv": "Only Parkinson's samples (20 samples) - test sensitivity", 
        "demo_edge_cases.csv": "Borderline cases (10 samples) - challenging predictions"
    }
    
    with open(demo_dir / "README.txt", 'w') as f:
        f.write("Demo Datasets for Parkinson's Prediction Testing\n")
        f.write("=" * 50 + "\n\n")
        for filename, description in summary.items():
            f.write(f"{filename}:\n  {description}\n\n")
        f.write("Usage:\n")
        f.write("1. Upload any CSV to your Streamlit app\n")
        f.write("2. The app will make predictions for all samples\n")
        f.write("3. Compare predictions with 'status' column (0=Healthy, 1=Parkinson's)\n")
    
    print(f"\nAll demo datasets saved to: {demo_dir}/")
    print("README.txt created with dataset descriptions")
    
    return demo_dir

if __name__ == "__main__":
    save_demo_data()