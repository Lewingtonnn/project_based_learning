import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
Database_URL = os.getenv("SyncDatabase_URL")

# Connect to the database and fetch data
if not Database_URL:
    raise ValueError("SyncDatabase_URL environment variable is not set.")
engine = create_engine(Database_URL)
df = pd.read_sql("""
    SELECT 
        property.state, 
        T1.bedrooms, 
        T1.bathrooms, 
        property.year_built, 
        property.property_reviews, 
        property.listing_verification, 
        T1.base_rent, 
        T1.sqft 
    FROM 
        pricing_and_floor_plans T1
    JOIN 
        property ON property.id = T1.property_id
""", engine)

# Convert appropriate columns to numeric, forcing errors to 'NaN'
# This handles cases where base_rent or sqft might be non-numeric (e.g., 'Call for Price')
df['base_rent'] = pd.to_numeric(df['base_rent'], errors='coerce')
df['sqft'] = pd.to_numeric(df['sqft'], errors='coerce')
df['year_built'] = pd.to_numeric(df['year_built'], errors='coerce')

# Drop rows with any NaN values after conversion
df.dropna(inplace=True)

# --------------------
# Define features and target variable
# ------------------------------------------
X = df[['bedrooms', 'bathrooms', 'year_built', 'property_reviews', 'sqft', 'state', 'listing_verification']]
y = df['base_rent']

# ---------------------------------
# Define preprocessing steps and build the pipeline
# ------------------------------------------
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Separate columns by data type
numerical_features = ['bedrooms', 'bathrooms', 'year_built', 'sqft', 'property_reviews']
categorical_features = ['state', 'listing_verification']

# Create preprocessor with ColumnTransformer
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numerical_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ])

# Create the full pipeline
model_pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', LinearRegression())
])

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Fit the pipeline on the training data
model_pipeline.fit(X_train, y_train)

# Make predictions on the test set
predictions = model_pipeline.predict(X_test)

# Evaluate the model
mse = mean_squared_error(y_test, predictions)
r2 = r2_score(y_test, predictions)

print(f"Mean Squared Error: {mse}")
print(f"R-squared: {r2}")

# Save the model pipeline
import joblib
model_filename = 'linear_regression_rent_model_pipeline.pkl'
joblib.dump(model_pipeline, model_filename)