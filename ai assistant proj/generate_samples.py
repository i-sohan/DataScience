import pandas as pd
import numpy as np
from pathlib import Path
import random
from datetime import datetime, timedelta

dataset_dir = Path(r"c:\Users\sohan\OneDrive\Desktop\Data science\ai assistant\datasets")
dataset_dir.mkdir(parents=True, exist_ok=True)

np.random.seed(42)
random.seed(42)

# 1. Sales Dataset (1000 records)
states_cities = {
    'Karnataka': ['Bangalore', 'Mysore', 'Hubli'],
    'Maharashtra': ['Mumbai', 'Pune', 'Nagpur'],
    'Tamil Nadu': ['Chennai', 'Coimbatore', 'Madurai'],
    'Delhi': ['Delhi', 'New Delhi'],
    'Telangana': ['Hyderabad', 'Warangal'],
    'Gujarat': ['Ahmedabad', 'Surat']
}

products_categories = {
    'Technology': [('Laptop', 65000, 12000), ('Monitor', 18000, 4500), ('Mouse', 800, 200), ('Keyboard', 1500, 400), ('Smartphone', 35000, 7000)],
    'Furniture': [('Ergonomic Chair', 12000, 3000), ('Standing Desk', 25000, 5500), ('Bookshelf', 8000, 1800)],
    'Office Supplies': [('Paper Ream', 300, 80), ('Binder', 250, 60), ('Gel Pen Box', 150, 40)]
}

customers = [f"Cust_{i:04d}" for i in range(1, 151)]

start_date = datetime(2025, 1, 1)
sales_data = []

for i in range(1, 1001):
    order_id = 1000 + i
    days_offset = random.randint(0, 365)
    order_date = start_date + timedelta(days=days_offset)
    
    state = random.choice(list(states_cities.keys()))
    city = random.choice(states_cities[state])
    
    category = random.choice(list(products_categories.keys()))
    product, base_price, base_profit = random.choice(products_categories[category])
    
    quantity = random.randint(1, 10)
    # Add slight variation
    variation = random.uniform(0.9, 1.1)
    sales = round(base_price * quantity * variation, 2)
    profit = round(base_profit * quantity * variation, 2)
    
    # Format currency string occasionally to test auto-cleaner e.g. ₹50,000 or raw numbers
    sales_str = f"₹{sales:,.2f}" if random.random() < 0.2 else sales
    
    sales_data.append({
        'OrderID': order_id,
        'Date': order_date.strftime('%Y-%m-%d') if random.random() < 0.8 else order_date.strftime('%d/%m/%Y'),
        'Customer': random.choice(customers),
        'State': state,
        'City': city,
        'Category': category,
        'Product': product,
        'Quantity': quantity,
        'Sales': sales_str,
        'Profit': profit,
        'PaymentMethod': random.choice(['UPI', 'Credit Card', 'Net Banking', 'Cash on Delivery'])
    })

df_sales = pd.DataFrame(sales_data)
# Inject a few nulls and duplicate rows to test auto cleaner
df_sales.loc[5, 'Sales'] = None
df_sales.loc[12, 'City'] = '  Bangalore  '  # Extra whitespace
df_sales = pd.concat([df_sales, df_sales.iloc[[20, 21]]], ignore_index=True)

df_sales.to_csv(dataset_dir / 'sample_sales.csv', index=False)
print(f"Generated sample_sales.csv with {len(df_sales)} rows.")

# 2. HR Attrition Dataset (500 records)
departments = ['Sales', 'R&D', 'Human Resources', 'Marketing', 'Finance']
roles = {
    'Sales': ['Sales Executive', 'Sales Manager'],
    'R&D': ['Research Scientist', 'Software Engineer', 'Lab Technician'],
    'Human Resources': ['HR Recruiter', 'HR Specialist'],
    'Marketing': ['Marketing Specialist', 'SEO Manager'],
    'Finance': ['Financial Analyst', 'Accountant']
}

hr_data = []
for i in range(1, 501):
    emp_id = f"EMP_{i:04d}"
    dept = random.choice(departments)
    role = random.choice(roles[dept])
    age = random.randint(22, 60)
    exp = max(1, age - random.randint(21, 26))
    income = round(25000 + exp * random.uniform(4000, 8000), 2)
    commute = random.randint(2, 45)
    
    # Attrition probability higher for Sales, long commute, lower income
    attr_prob = 0.1
    if dept == 'Sales': attr_prob += 0.15
    if commute > 25: attr_prob += 0.15
    if income < 45000: attr_prob += 0.1
    
    attrition = 'Yes' if random.random() < attr_prob else 'No'
    
    hr_data.append({
        'EmployeeID': emp_id,
        'Department': dept,
        'JobRole': role,
        'Age': age,
        'MonthlyIncome': f"₹{income:,.0f}" if random.random() < 0.3 else income,
        'YearsAtCompany': random.randint(1, min(15, exp)),
        'CommuteDistanceKM': commute,
        'OverTime': random.choice(['Yes', 'No']),
        'JobSatisfaction': random.randint(1, 5),
        'Attrition': attrition
    })

df_hr = pd.DataFrame(hr_data)
df_hr.to_csv(dataset_dir / 'sample_hr.csv', index=False)
print(f"Generated sample_hr.csv with {len(df_hr)} rows.")

# 3. Healthcare Patient Dataset (500 records)
health_data = []
for i in range(1, 501):
    p_id = f"PAT_{i:04d}"
    age = random.randint(15, 85)
    gender = random.choice(['Male', 'Female'])
    bmi = round(random.uniform(18.5, 38.0), 1)
    bp_sys = random.randint(100, 170)
    glucose = random.randint(70, 220)
    
    risk_score = 0
    if age > 50: risk_score += 1
    if bmi > 28: risk_score += 1
    if glucose > 140: risk_score += 2
    
    risk = 'High' if risk_score >= 3 else ('Moderate' if risk_score >= 1 else 'Low')
    charges = round(15000 + age * 250 + glucose * 150 + random.uniform(2000, 10000), 2)
    
    health_data.append({
        'PatientID': p_id,
        'Age': age,
        'Gender': gender,
        'City': random.choice(['Bangalore', 'Mumbai', 'Delhi', 'Chennai', 'Hyderabad']),
        'BMI': bmi,
        'BloodPressure': bp_sys,
        'GlucoseLevel': glucose,
        'DiabetesRisk': risk,
        'HospitalCharges': charges
    })

df_health = pd.DataFrame(health_data)
df_health.to_csv(dataset_dir / 'sample_healthcare.csv', index=False)
print(f"Generated sample_healthcare.csv with {len(df_health)} rows.")
