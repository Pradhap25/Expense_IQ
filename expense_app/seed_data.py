"""Run this script to populate the database with sample data for testing."""
from app import create_app
from models import db, User, Transaction, Category, Subcategory, Budget
from datetime import datetime, timedelta
import random

app = create_app()

with app.app_context():
    # Check if demo user exists
    demo = User.query.filter_by(email='demo@example.com').first()
    if not demo:
        demo = User(username='demo', email='demo@example.com')
        demo.set_password('demo1234')
        db.session.add(demo)
        db.session.commit()
        print("Created demo user: demo@example.com / demo1234")

        # Seed default categories
        from routes.auth import _seed_default_categories
        _seed_default_categories(demo)
        print("Seeded categories")

    cats = Category.query.filter_by(user_id=demo.id).all()
    exp_cats = [c for c in cats if c.type == 'expense']
    inc_cats = [c for c in cats if c.type == 'income']

    # Generate 6 months of transactions
    now = datetime.utcnow()
    tx_count = 0
    for month_offset in range(5, -1, -1):
        m = now.month - month_offset
        y = now.year
        if m <= 0:
            m += 12
            y -= 1
        days_in_month = 28 if m == 2 else (30 if m in [4, 6, 9, 11] else 31)

        # Monthly salary
        inc_cat = random.choice(inc_cats)
        sub = random.choice(inc_cat.subcategories) if inc_cat.subcategories else None
        salary = Transaction(
            amount=round(random.uniform(45000, 65000), 2),
            type='income', category_id=inc_cat.id,
            subcategory_id=sub.id if sub else None,
            notes='Monthly salary',
            user_id=demo.id,
            date=datetime(y, m, 1)
        )
        db.session.add(salary)
        tx_count += 1

        # Random expenses (15-25 per month)
        for _ in range(random.randint(15, 25)):
            cat = random.choice(exp_cats)
            sub = random.choice(cat.subcategories) if cat.subcategories else None
            day = random.randint(1, days_in_month)
            hour = random.randint(8, 22)
            amount_ranges = {
                'Food & Dining': (50, 800), 'Transport': (20, 500),
                'Shopping': (200, 3000), 'Bills & Utilities': (500, 2000),
                'Health': (100, 2000), 'Entertainment': (50, 1000), 'Education': (500, 5000)
            }
            low, high = amount_ranges.get(cat.name, (100, 1000))
            db.session.add(Transaction(
                amount=round(random.uniform(low, high), 2),
                type='expense', category_id=cat.id,
                subcategory_id=sub.id if sub else None,
                notes=random.choice([None, 'Regular expense', 'Monthly bill', 'Weekly purchase']),
                user_id=demo.id,
                date=datetime(y, m, day, hour, random.randint(0, 59))
            ))
            tx_count += 1

    db.session.commit()
    print(f"Added {tx_count} sample transactions")

    # Set budgets for current month
    budget_map = {'Food & Dining': 8000, 'Transport': 3000, 'Shopping': 5000, 'Bills & Utilities': 4000, 'Health': 2000, 'Entertainment': 2000, 'Education': 3000}
    for cat in exp_cats:
        if cat.name in budget_map:
            existing = Budget.query.filter_by(user_id=demo.id, category_id=cat.id, month=now.month, year=now.year).first()
            if not existing:
                db.session.add(Budget(amount=budget_map[cat.name], month=now.month, year=now.year, category_id=cat.id, user_id=demo.id))
    db.session.commit()
    print("Set monthly budgets")
    print("\n✅ Done! Login at http://localhost:5000 with demo@example.com / demo1234")
