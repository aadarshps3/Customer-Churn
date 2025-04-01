import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib

# Generate synthetic churn data
np.random.seed(42)
n_samples = 1000
data = {
    'tenure': np.random.randint(1, 72, n_samples),
    'monthly_charges': np.random.uniform(20, 120, n_samples),
    'total_charges': np.random.uniform(20, 5000, n_samples),
    'contract_type': np.random.choice([0, 1], n_samples)  # 0 = Month-to-month, 1 = One year
}
df = pd.DataFrame(data)

# Simple churn rule: higher tenure & one-year contract = less likely to churn
df['churn'] = ((df['tenure'] < 12) & (df['monthly_charges'] > 80) & (df['contract_type'] == 0)).astype(int)

# Features and target
X = df[['tenure', 'monthly_charges', 'total_charges', 'contract_type']]
y = df['churn']

# Split and scale data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train model
model = LogisticRegression(random_state=42)
model.fit(X_train_scaled, y_train)

# Save model and scaler
joblib.dump(model, 'churn/churn_model.pkl')
joblib.dump(scaler, 'churn/scaler.pkl')

print("Model and scaler saved successfully!")