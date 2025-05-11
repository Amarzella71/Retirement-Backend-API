from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import datetime
import math
import pdfkit
import smtplib
from email.message import EmailMessage
import matplotlib.pyplot as plt
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RetirementForm(BaseModel):
    fullName: str
    dob: datetime.date
    gender: str
    maritalStatus: str
    dependents: int
    email: EmailStr
    phone: str
    address: str

    employmentStatus: str
    occupation: str
    employer: Optional[str] = None
    grossIncome: float
    netIncome: float
    retirementAge: int
    desiredRetirementIncome: float

    superFundName: str
    superBalance: float
    contributionType: str
    annualContributions: float
    investmentOption: str
    fees: Optional[str] = None
    multipleSuper: str

    primaryResidence: float
    otherProperty: float
    cashSavings: float
    shares: float
    managedFunds: float
    businessInterests: float
    personalProperty: float

    mortgage: float
    propertyLoans: float
    personalLoans: float
    creditDebt: float
    otherDebts: float

    retirementLocation: str
    retirementActivities: str
    livingExpenses: float
    downsizeProperty: str
    reverseMortgage: str

    lifeInsurance: str
    incomeProtection: str
    tpdInsurance: str
    hasWill: str
    powerOfAttorney: str

    inheritance: float
    dependentsSupport: str
    healthConcerns: Optional[str] = None
    otherGoals: Optional[str] = None

    confirmInfo: bool
    consentEmail: bool

def calculate_retirement_projection(current_age: int, retirement_age: int, current_balance: float, annual_contribution: float, growth_rate: float = 0.06, inflation_rate: float = 0.025):
    n_years = retirement_age - current_age
    real_growth_rate = (1 + growth_rate) / (1 + inflation_rate) - 1
    yearly_balances = []
    balance = current_balance
    for year in range(n_years):
        balance *= (1 + real_growth_rate)
        balance += annual_contribution
        yearly_balances.append(round(balance, 2))
    return {
        "years_until_retirement": n_years,
        "real_growth_rate": real_growth_rate,
        "projected_super_balance": round(balance, 2),
        "yearly_balances": yearly_balances
    }

def create_projection_chart(name: str, balances: list, chart_path: str):
    years = list(range(1, len(balances) + 1))
    plt.figure(figsize=(10, 6))
    plt.plot(years, balances, marker='o')
    plt.title(f"Projected Super Balance for {name}")
    plt.xlabel("Years Until Retirement")
    plt.ylabel("Balance ($)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()

def generate_pdf_report(name: str, age: int, projection: dict, file_path: str, chart_path: str):
    html_content = f"""
    <html>
      <head><style>body {{ font-family: Arial; }}</style></head>
      <body>
        <h1>Retirement Planning Summary</h1>
        <p><strong>Name:</strong> {name}</p>
        <p><strong>Current Age:</strong> {age}</p>
        <p><strong>Years Until Retirement:</strong> {projection['years_until_retirement']}</p>
        <p><strong>Projected Super Balance:</strong> ${projection['projected_super_balance']:,.2f}</p>
        <p><strong>Real Growth Rate:</strong> {projection['real_growth_rate']:.2%}</p>
        <h2>Projection Chart</h2>
        <img src="{chart_path}" width="600" />
      </body>
    </html>
    """
    pdfkit.from_string(html_content, file_path)

def send_email_with_attachment(to_email: str, subject: str, body: str, file_path: str):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = "noreply@yourdomain.com"
    msg['To'] = to_email
    msg.set_content(body)
    with open(file_path, 'rb') as f:
        file_data = f.read()
        msg.add_attachment(file_data, maintype='application', subtype='pdf', filename='retirement_summary.pdf')
    with smtplib.SMTP('localhost') as smtp:
        smtp.send_message(msg)

@app.post("/submit-retirement-form")
async def submit_form(data: RetirementForm):
    if not data.confirmInfo or not data.consentEmail:
        raise HTTPException(status_code=400, detail="Consent not given.")
    today = datetime.date.today()
    age = today.year - data.dob.year - ((today.month, today.day) < (data.dob.month, data.dob.day))
    projection = calculate_retirement_projection(
        current_age=age,
        retirement_age=data.retirementAge,
        current_balance=data.superBalance,
        annual_contribution=data.annualContributions
    )
    chart_path = f"/tmp/{data.fullName.replace(' ', '_')}_chart.png"
    file_path = f"/tmp/{data.fullName.replace(' ', '_')}_retirement_report.pdf"
    create_projection_chart(data.fullName, projection["yearly_balances"], chart_path)
    generate_pdf_report(data.fullName, age, projection, file_path, chart_path)
    send_email_with_attachment(
        to_email=data.email,
        subject="Your Retirement Planning Summary",
        body="Attached is your personalised retirement planning summary.",
        file_path=file_path
    )
    if os.path.exists(chart_path):
        os.remove(chart_path)
    return {
        "message": "Form received and report sent successfully",
        "name": data.fullName,
        "current_age": age,
        "retirement_projection": projection
    }
