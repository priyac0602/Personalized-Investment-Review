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

    if row["REALESTATE"] == 0 and row["NETASSETS"] > 75000 and row["AGE"] > 35:
        suggestions.append("🏠 Consider investing in Real Estate for long-term asset growth.")

    if row["PRIVATEEQUITY"] == 0 and row["RISKPROFILE"] >= 0.7:
        suggestions.append("🚀 Explore Private Equity to align with your high-risk profile.")

    if row["ETFTECH"] == 0 and row["CREDITSCORE"] > 700 and row["RISKPROFILE"] >= 0.5:
        suggestions.append("💻 Add ETF Tech for diversified yet growth-oriented exposure.")

    if row["RISKPROFILE"] <= 0.3 and row["REALESTATE"] == 0:
        suggestions.append("🛡️ As a low-risk customer, Real Estate or bonds might suit you.")

    invested = sum([row[col] for col in ["ETFTECH", "ETFHEALTH", "ETFMED", "REALESTATE", "PRIVATEEQUITY"]])
    if invested <= 1:
        suggestions.append("📊 Your investments are highly concentrated. Diversify more.")

    return "\n\n".join(suggestions) if suggestions else "✅ Portfolio looks balanced."

def detect_red_flags(row):
    flags = []

    if row["RISKPROFILE"] > 0.7 and row["CREDITSCORE"] < 600:
        flags.append("⚠️ High risk profile with poor credit score — possible default risk.")

    if row["NETASSETS"] < 10000 and row["PORTFOLIORETURN"] < 0.05:
        flags.append("📉 Low assets and low return — consider reevaluating financial plan.")

    if row["AGE"] > 55 and invested_products(row) == 0:
        flags.append("🔻 Older customer with no investments — missed wealth opportunities.")

    if row["AGE"] < 25 and has_high_risk(row):
        flags.append("🧨 Young customer taking high risk — consider financial literacy programs.")

    return "\n\n".join(flags) if flags else "🟢 No critical red flags detected."

def invested_products(row):
    return sum([row[col] for col in ["ETFTECH", "ETFHEALTH", "ETFMED", "REALESTATE", "PRIVATEEQUITY"]])

def has_high_risk(row):
    return row["RISKPROFILE"] > 0.6

# ----------------- Dashboard UI Section --------------------

st.subheader("📌 Personalized Investment Review")

# Select Customer
selected_id = st.selectbox("Select Customer ID", df["CUSTOMERID"].unique())
customer = df[df["CUSTOMERID"] == selected_id].iloc[0]

# Display Basic Info
st.markdown("### 🧾 Customer Profile")
st.write({
    "Age": customer["AGE"],
    "Gender": customer["GENDER"],
    "Country": customer["COUNTRY"],
    "Credit Score": customer["CREDITSCORE"],
    "Risk Profile": customer["RISKPROFILE"],
    "Portfolio Return": customer["PORTFOLIORETURN"],
    "Net Assets": customer["NETASSETS"]
})

# Display Investment Status
st.markdown("### 💼 Current Investment Holdings")
st.write({
    "ETF Tech": customer["ETFTECH"],
    "ETF Health": customer["ETFHEALTH"],
    "ETF Med": customer["ETFMED"],
    "Real Estate": customer["REALESTATE"],
    "Private Equity": customer["PRIVATEEQUITY"]
})

# Show Smart Suggestions
st.markdown("### ✅ Suggestions Based on Profile")
st.success(investment_suggestions(customer))

# Show Red Flags
st.markdown("### 🛑 Red Flag Warnings")
st.warning(detect_red_flags(customer))
