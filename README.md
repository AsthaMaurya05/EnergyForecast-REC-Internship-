⚡ Energy Forecast Dashboard

An interactive Streamlit-based dashboard for forecasting state-wise power consumption in India.
Built with Facebook Prophet, the app provides forecasts, trends, and insights into electricity demand and supply.

🚀 Features

🔐 User Authentication (Sign Up & Login with password hashing)

📝 Login History Tracking (login_logs.json)

📊 Forecast Dashboard with:

Energy Met trend

Requirement vs. Met comparison

Deficit trend

Forecast with confidence intervals

⏳ Personal Forecast History saved per user

📥 (Optional) Export forecast results to CSV

📌 Data sourced from Grid India

🛠️ Tech Stack

Python

Streamlit (UI)

Pandas, Matplotlib (Data handling & visualization)

Facebook Prophet (Forecasting)

bcrypt (Password hashing)

JSON (User data, logs, forecast history)

📂 Project Structure
REC PROJECT/
│── EnergyForecast.py        # Main Streamlit app
│── All_states (version 1).csv  # Dataset
│── users.json               # User credentials (hashed)
│── login_logs.json           # Login logs
│── current_user.json         # Active user session
│── user_history_<username>.json  # Forecast history per user
│── requirements.txt          # Python dependencies
│── users.db                  # (Currently unused, SQLite version)


📦 Installation

Clone the repository

git clone https://github.com/your-username/energy-forecast-dashboard.git
cd energy-forecast-dashboard


Create & activate virtual environment (optional but recommended)

python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows


Install dependencies

pip install -r requirements.txt

▶️ Run the App
streamlit run EnergyForecast.py


Then open the local URL shown in terminal (usually http://localhost:8501).

📊 Usage

Sign up with a new account.

Login using your credentials.

Select Region and State from the sidebar.

Choose forecast duration (3–12 months).

Explore:

Trends & comparisons

Prophet forecast plots

Forecast history (saved per user)


🔮 Future Improvements

Switch from JSON to SQLite (users.db) for better scalability.

Add download option for forecast CSVs.

Improve frontend design for better user experience.

Deploy on Streamlit Cloud / Heroku / AWS.
