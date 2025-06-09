import streamlit as st
import pandas as pd
import snowflake.connector

conn=snowflake.connector.connect(
    user=st.secrets["snowflake"]["user"],
    password=st.secrets["snowflake"]["password"],
    account=st.secrets["snowflake"]["account"],
    warehouse=st.secrets["snowflake"]["warehouse"],
    database=st.secrets["snowflake"]["database"],
    schema=st.secrets["snowflake"]["schema"]
)

query="SELECT * FROM wealth_sch.customer_clean"
df=pd.read_sql(query,conn)

def investment_suggestions(row):
    suggestions = []

    if row["RealEstate"] == 0 and row["Net Assets"] > 75000 and row["Age"] > 35:
        suggestions.append("🏠 Consider investing in Real Estate for long-term asset growth.")

    if row["PrivateEquity"] == 0 and row["Risk_Profile"] >= 0.7:
        suggestions.append("🚀 Explore Private Equity to align with your high-risk profile.")

    if row["ETF Tech"] == 0 and row["CreditScore"] > 700 and row["Risk_Profile"] >= 0.5:
        suggestions.append("💻 Add ETF Tech for diversified yet growth-oriented exposure.")

    if row["Risk_Profile"] <= 0.3 and row["RealEstate"] == 0:
        suggestions.append("🛡️ As a low-risk customer, Real Estate or bonds might suit you.")

    invested = sum([row[col] for col in ["ETF Tech", "ETF Health", "ETF Med", "RealEstate", "PrivateEquity"]])
    if invested <= 1:
        suggestions.append("📊 Your investments are highly concentrated. Diversify more.")

    return "\n\n".join(suggestions) if suggestions else "✅ Portfolio looks balanced."

def detect_red_flags(row):
    flags = []

    if row["Risk_Profile"] > 0.7 and row["CreditScore"] < 600:
        flags.append("⚠️ High risk profile with poor credit score — possible default risk.")

    if row["Net Assets"] < 10000 and row["Portfolio_Return"] < 0.05:
        flags.append("📉 Low assets and low return — consider reevaluating financial plan.")

    if row["Age"] > 55 and invested_products(row) == 0:
        flags.append("🔻 Older customer with no investments — missed wealth opportunities.")

    if row["Age"] < 25 and has_high_risk(row):
        flags.append("🧨 Young customer taking high risk — consider financial literacy programs.")

    return "\n\n".join(flags) if flags else "🟢 No critical red flags detected."

def invested_products(row):
    return sum([row[col] for col in ["ETF Tech", "ETF Health", "ETF Med", "RealEstate", "PrivateEquity"]])

def has_high_risk(row):
    return row["Risk_Profile"] > 0.6

# ----------------- Dashboard UI Section --------------------

st.subheader("📌 Personalized Investment Review")

# Select Customer
selected_id = st.selectbox("Select Customer ID", df["CustomerID"].unique())
customer = df[df["CustomerID"] == selected_id].iloc[0]

# Display Basic Info
st.markdown("### 🧾 Customer Profile")
st.write({
    "Age": customer["Age"],
    "Gender": customer["Gender"],
    "Country": customer["Country"],
    "Credit Score": customer["CreditScore"],
    "Risk Profile": customer["Risk_Profile"],
    "Portfolio Return": customer["Portfolio_Return"],
    "Net Assets": customer["Net Assets"]
})

# Display Investment Status
st.markdown("### 💼 Current Investment Holdings")
st.write({
    "ETF Tech": customer["ETF Tech"],
    "ETF Health": customer["ETF Health"],
    "ETF Med": customer["ETF Med"],
    "Real Estate": customer["RealEstate"],
    "Private Equity": customer["PrivateEquity"]
})

# Show Smart Suggestions
st.markdown("### ✅ Suggestions Based on Profile")
st.success(investment_suggestions(customer))

# Show Red Flags
st.markdown("### 🛑 Red Flag Warnings")
st.warning(detect_red_flags(customer))
