from datetime import date, datetime
from pathlib import Path
import csv

import pandas as pd
from flask import Flask, flash, redirect, render_template, request, url_for
from sklearn.linear_model import LinearRegression

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "expenses.csv"

app = Flask(__name__)
app.secret_key = "replace-this-with-an-environment-secret-before-production"

CATEGORIES = [
    "Food", "Transport", "Housing", "Utilities", "Shopping",
    "Health", "Education", "Entertainment", "Savings", "Other"
]
FIELDS = ["date", "description", "category", "amount"]


def ensure_data_file():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        # Fictional demonstration transactions; replace with your own test data.
        examples = [
            ["2026-08-03", "Groceries", "Food", "520.00"],
            ["2026-08-06", "Taxi and bus", "Transport", "260.00"],
            ["2026-08-10", "Electricity", "Utilities", "430.00"],
            ["2026-08-15", "Takeaway", "Food", "180.00"],
            ["2026-09-02", "Groceries", "Food", "610.00"],
            ["2026-09-05", "Transport", "Transport", "310.00"],
            ["2026-09-08", "Rent contribution", "Housing", "2200.00"],
            ["2026-09-13", "Mobile data", "Utilities", "250.00"],
            ["2026-09-18", "Clothing", "Shopping", "450.00"],
            ["2026-10-02", "Groceries", "Food", "690.00"],
            ["2026-10-05", "Transport", "Transport", "340.00"],
            ["2026-10-07", "Electricity", "Utilities", "390.00"],
            ["2026-10-10", "Streaming", "Entertainment", "120.00"],
            ["2026-10-14", "Pharmacy", "Health", "160.00"],
        ]
        with DATA_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(FIELDS)
            writer.writerows(examples)


def read_expenses():
    ensure_data_file()
    try:
        df = pd.read_csv(DATA_FILE)
        if df.empty:
            return pd.DataFrame(columns=FIELDS)
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date", "amount"])
        return df
    except (pd.errors.EmptyDataError, FileNotFoundError):
        return pd.DataFrame(columns=FIELDS)


def write_expense(expense_date, description, category, amount):
    ensure_data_file()
    with DATA_FILE.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([expense_date, description, category, f"{amount:.2f}"])


def make_insights(df):
    insights = []
    if df.empty:
        return ["Add some expenses to see personalized spending insights."]
    total = float(df["amount"].sum())
    by_category = df.groupby("category")["amount"].sum().sort_values(ascending=False)
    if not by_category.empty and total > 0:
        category = str(by_category.index[0])
        share = float(by_category.iloc[0]) / total * 100
        insights.append(f"{category} is your largest recorded spending category ({share:.1f}% of all expenses shown).")
    monthly = df.assign(month=df["date"].dt.to_period("M").astype(str)).groupby("month")["amount"].sum().sort_index()
    if len(monthly) >= 2:
        previous, latest = float(monthly.iloc[-2]), float(monthly.iloc[-1])
        change = latest - previous
        if previous > 0:
            pct = abs(change) / previous * 100
            if change > 0:
                insights.append(f"Recorded spending increased by {pct:.1f}% from {monthly.index[-2]} to {monthly.index[-1]}.")
            elif change < 0:
                insights.append(f"Recorded spending decreased by {pct:.1f}% from {monthly.index[-2]} to {monthly.index[-1]}.")
            else:
                insights.append("Recorded spending stayed the same between the two latest months.")
    if not insights:
        insights.append("Keep recording expenses across several months to reveal useful trends.")
    insights.append("Tip: review recurring subscriptions and compare essential versus optional spending before changing your budget.")
    return insights


def forecast_monthly_spend(df):
    """Illustrative one-month forecast using a simple linear regression."""
    if df.empty:
        return None, "Add expenses before generating a forecast."
    monthly = (
        df.assign(month=df["date"].dt.to_period("M").astype(str))
        .groupby("month")["amount"].sum()
        .sort_index()
    )
    if len(monthly) < 3:
        return None, "Record expenses in at least three different months to enable a basic forecast."
    x = list(range(len(monthly)))
    model = LinearRegression()
    model.fit(pd.DataFrame({"month_index": x}), monthly.values)
    prediction = float(model.predict(pd.DataFrame({"month_index": [len(monthly)]}))[0])
    return max(0.0, prediction), f"Based on the trend across {len(monthly)} recorded months."


@app.route("/", methods=["GET"])
def dashboard():
    df = read_expenses()
    total = float(df["amount"].sum()) if not df.empty else 0.0
    this_month = pd.Period(date.today(), freq="M")
    month_df = df[df["date"].dt.to_period("M") == this_month] if not df.empty else df
    month_total = float(month_df["amount"].sum()) if not month_df.empty else 0.0

    if not df.empty:
        category_totals = df.groupby("category")["amount"].sum().sort_values(ascending=False)
        categories = [
            {"name": str(name), "amount": round(float(value), 2),
             "share": round(float(value) / total * 100, 1) if total else 0}
            for name, value in category_totals.items()
        ]
        monthly_totals = (
            df.assign(month=df["date"].dt.to_period("M").astype(str))
            .groupby("month")["amount"].sum().sort_index()
        )
        months = [{"month": str(m), "amount": round(float(v), 2)} for m, v in monthly_totals.items()]
        recent = df.sort_values("date", ascending=False).head(10).copy()
        recent["date"] = recent["date"].dt.strftime("%Y-%m-%d")
        recent["amount"] = recent["amount"].map(lambda v: f"{v:,.2f}")
        recent_expenses = recent.to_dict("records")
    else:
        categories, months, recent_expenses = [], [], []

    forecast, forecast_note = forecast_monthly_spend(df)
    return render_template(
        "index.html",
        total=total,
        month_total=month_total,
        expense_count=len(df),
        categories=categories,
        months=months,
        recent_expenses=recent_expenses,
        insights=make_insights(df),
        forecast=forecast,
        forecast_note=forecast_note,
        currency="R",
        today=date.today().isoformat(),
        category_options=CATEGORIES,
    )


@app.route("/add", methods=["POST"])
def add_expense():
    expense_date = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "").strip()
    amount_raw = request.form.get("amount", "").strip()

    try:
        parsed_date = datetime.strptime(expense_date, "%Y-%m-%d").date()
        amount = float(amount_raw)
        if amount <= 0 or amount > 100_000_000:
            raise ValueError
        if not description or len(description) > 100:
            raise ValueError
        if category not in CATEGORIES:
            raise ValueError
    except (ValueError, TypeError):
        flash("Please enter a valid date, description, category, and positive amount.", "error")
        return redirect(url_for("dashboard"))

    write_expense(parsed_date.isoformat(), description, category, amount)
    flash("Expense added successfully.", "success")
    return redirect(url_for("dashboard"))


@app.route("/delete/<int:row_id>", methods=["POST"])
def delete_expense(row_id):
    df = read_expenses()
    if row_id < 0 or row_id >= len(df):
        flash("Expense was not found.", "error")
        return redirect(url_for("dashboard"))
    df = df.reset_index(drop=True).drop(index=row_id)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df["amount"] = df["amount"].map(lambda v: f"{v:.2f}")
    df[FIELDS].to_csv(DATA_FILE, index=False)
    flash("Expense deleted.", "success")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    ensure_data_file()
    app.run(debug=True)
