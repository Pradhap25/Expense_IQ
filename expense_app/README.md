# 💡 ExpenseIQ — AI-Powered Expense Management System

A full-stack expense management system with AI insights, ML-based predictions, budget tracking, and rich analytics — built with Flask, SQLite, and vanilla JS.

---

## 🚀 Quick Start

### Mac / Linux
```bash
cd expense_app
chmod +x run.sh
./run.sh
```

### Windows
```cmd
cd expense_app
run.bat
```

Both scripts will:
1. Create a Python virtual environment
2. Install all dependencies
3. Seed sample data (6 months of transactions)
4. Start the server at **http://localhost:5000**

**Demo credentials:** `demo@example.com` / `demo1234`

---

## 📁 Project Structure

```
expense_app/
├── app.py                  # Flask app factory & entry point
├── models.py               # SQLAlchemy models (User, Transaction, Category, Subcategory, Budget)
├── seed_data.py            # Demo data generator
├── requirements.txt        # Python dependencies
├── run.sh                  # Mac/Linux startup script
├── run.bat                 # Windows startup script
│
├── routes/
│   ├── __init__.py
│   ├── auth.py             # Register, login, logout + default category seeding
│   ├── main.py             # Dashboard page route
│   ├── transactions.py     # CRUD + CSV export
│   ├── categories.py       # Category & subcategory management
│   ├── reports.py          # Daily/weekly/monthly/yearly reports
│   ├── budgets.py          # Budget CRUD + alerts
│   └── insights.py         # AI insights + ML expense prediction
│
├── templates/
│   ├── auth.html           # Login / Register page
│   └── dashboard.html      # Main application shell
│
└── static/
    ├── css/
    │   └── dashboard.css   # Full dark-theme UI styles
    └── js/
        └── dashboard.js    # All client-side logic (charts, API calls, state)
```

---

## 🗄️ Database Schema

| Table | Key Columns |
|---|---|
| `users` | id, username, email, password_hash, created_at |
| `categories` | id, name, type (income/expense), icon, color, user_id |
| `subcategories` | id, name, category_id |
| `transactions` | id, amount, type, date, category_id, subcategory_id, notes, user_id |
| `budgets` | id, amount, month, year, category_id, user_id |

---

## 🔌 REST API Reference

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login |
| POST | `/auth/logout` | Logout |

### Transactions
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/transactions/` | List (paginated, filterable) |
| POST | `/api/transactions/` | Add transaction |
| PUT | `/api/transactions/<id>` | Update transaction |
| DELETE | `/api/transactions/<id>` | Delete transaction |
| GET | `/api/transactions/balance` | Get income/expense/balance totals |
| GET | `/api/transactions/export/csv` | Download CSV |

**Query params for GET /:** `page`, `per_page`, `type`, `category_id`, `start_date`, `end_date`

### Categories
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/categories/` | List categories (with subcategories) |
| POST | `/api/categories/` | Create category |
| PUT | `/api/categories/<id>` | Update category |
| DELETE | `/api/categories/<id>` | Delete category |
| POST | `/api/categories/<id>/subcategories` | Add subcategory |
| DELETE | `/api/categories/subcategories/<id>` | Delete subcategory |

### Reports
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/reports/daily` | Today's report |
| GET | `/api/reports/weekly` | This week's report |
| GET | `/api/reports/monthly?month=&year=` | Monthly report |
| GET | `/api/reports/yearly?year=` | Yearly report |
| GET | `/api/reports/chart/monthly-trend` | 12-month trend data |

### Budgets
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/budgets/?month=&year=` | List budgets with progress |
| POST | `/api/budgets/` | Set budget |
| DELETE | `/api/budgets/<id>` | Remove budget |
| GET | `/api/budgets/alerts` | Get budget & balance alerts |

### AI Insights
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/insights/` | Rule-based spending insights |
| GET | `/api/insights/predict` | Linear regression prediction |

---

## ✨ Features

- **Authentication** — Register/login with bcrypt password hashing + Flask-Login sessions
- **Transactions** — Add, edit, delete income & expenses with category, subcategory, date, notes
- **Real-time Balance** — Income, expense, and net balance calculated on every request
- **Dynamic Categories** — Create custom categories and subcategories with icons and colors
- **10 Default Categories** — Pre-seeded for new users (Food, Transport, Shopping, etc.)
- **Reports** — Daily / weekly / monthly / yearly breakdowns with Chart.js visualizations
- **Budget Tracking** — Set per-category monthly budgets with live progress bars
- **Alerts** — Automatic warnings when budgets exceed 80% or balance goes negative
- **AI Insights** — 6+ rule-based patterns (spending spikes, savings rate, weekend patterns)
- **ML Prediction** — Linear regression model predicts next month's expenses
- **CSV Export** — Download all transactions as CSV
- **Responsive Design** — Works on mobile and desktop

---

## 🛠️ Manual Setup (without run scripts)

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python seed_data.py             # Optional: load demo data
python app.py
```

---

## 🔧 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `dev-secret-key-change-in-prod` | Flask session key — **change in production** |
| `DATABASE_URL` | `sqlite:///expense_manager.db` | Database URI |

---

## 📦 Dependencies

- **Flask** — Web framework
- **Flask-SQLAlchemy** — ORM
- **Flask-Login** — Session management
- **Flask-Bcrypt** — Password hashing
- **NumPy** — Linear regression for expense prediction
- **Chart.js** (CDN) — Charts and visualizations
- **Google Fonts** (CDN) — Syne + DM Sans typography
