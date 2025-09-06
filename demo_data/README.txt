Demo Datasets for Parkinson's Prediction Testing
==================================================

demo_small.csv:
  Small mixed dataset (10 samples) - good for quick testing

demo_large.csv:
  Larger mixed dataset (50 samples) - better for evaluation

demo_healthy_only.csv:
  Only healthy samples (20 samples) - test specificity

demo_parkinsons_only.csv:
  Only Parkinson's samples (20 samples) - test sensitivity

demo_edge_cases.csv:
  Borderline cases (10 samples) - challenging predictions

Usage:
1. Upload any CSV to your Streamlit app
2. The app will make predictions for all samples
3. Compare predictions with 'status' column (0=Healthy, 1=Parkinson's)
