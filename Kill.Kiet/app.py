from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.impute import SimpleImputer

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB Connection
client = MongoClient("mongodb+srv://sairock:%40%40sai143@cluster0.3p1ne.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['food_delivery']
users_collection = db['users']

# Load and Clean Data
data = pd.read_csv(r'C:\Users\hi\OneDrive\Documents\Kill.Kiet\food.csv')

data.columns = data.columns.str.strip()  # Clean column names

# Handle missing values
imputer = SimpleImputer(strategy='mean')

data = pd.get_dummies(data, 
                      columns=['Weather', 'Traffic_Level', 'Time_of_Day', 'Vehicle_Type'],
                      drop_first=True)

data.iloc[:, :] = imputer.fit_transform(data)

X = data.drop(['Order_ID', 'Delivery_Time_min'], axis=1)
y = data['Delivery_Time_min']

# Train Model
model = LinearRegression()
model.fit(X, y)

@app.route('/')
def home():
    if 'email' in session:
        return render_template('home.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = users_collection.find_one({"email": email, "password": password})
        if user:
            session['email'] = email
            return redirect(url_for('home'))
        else:
            return "Invalid Credentials"

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if users_collection.find_one({"email": email}):
            return "Email already registered!"

        users_collection.insert_one({
            "name": name,
            "email": email,
            "password": password
        })

        return "Registration Successful"

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('login'))

@app.route('/about')
def about():
    if 'email' in session:
        return render_template('about.html')
    return redirect(url_for('login'))

@app.route('/predict', methods=['POST'])
def predict():
    if 'email' not in session:
        return redirect(url_for('login'))

    try:
        input_data = pd.DataFrame([{  
            'Distance_km': float(request.form.get('distance')),
            'Weather_Rainy': 1 if request.form.get('weather') == 'Rainy' else 0,
            'Traffic_High': 1 if request.form.get('traffic') == 'High' else 0,
            'Time_of_Day_Evening': 1 if request.form.get('time_of_day') == 'Evening' else 0,
            'Vehicle_Type_Car': 1 if request.form.get('vehicle_type') == 'Car' else 0,
            'Preparation_Time_min': float(request.form.get('prep_time')),
            'Courier_Experience_yrs': float(request.form.get('experience'))
        }]).reindex(columns=X.columns, fill_value=0)

        prediction = model.predict(input_data)[0]
        return render_template('predict.html', prediction=round(prediction, 2))

    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/contact')
def contact():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)
 