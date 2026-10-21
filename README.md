# AI Expense Insights Assistant

A Flask-based personal expense dashboard demonstrating data analysis, simple regression forecasting, and rule-based spending insights.

## Features
- Add expenses with date, category, description, and amount (South African rand, R).
- Review totals and recent transactions.
- View spending by category.
- Read summaries of category and month-to-month spending.
- Estimate the next month's spending using linear regression when at least three months of data exist.

## Run on Windows with VS Code

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

## Deploy on Render

1. Push this project to GitHub.
2. Create a Render Web Service and connect the repository.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Deploy.

## Important deployment note
The demo stores transactions in `data/expenses.csv`. Many free web-service instances use an ephemeral filesystem, so changes may be lost after redeployment or service restart. Do not enter real or sensitive financial information. For durable multi-user production storage, use a managed database and add authentication, authorization, CSRF protection, secure secrets, and backups.

## Responsible AI
The forecast is a simple illustrative linear-regression model, not professional financial advice. It can be unreliable when data is limited or spending patterns change. Insights describe the recorded data and should not be treated as instructions to make financial decisions.
