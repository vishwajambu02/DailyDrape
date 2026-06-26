"""
One-time fix: adds the missing is_admin column to the users table,
then makes one account an admin.

USAGE:
  1. Save this file as fix_admin_column.py in your DailyDrape root
     (same folder as app.py and models.py).
  2. Edit YOUR_EMAIL below to the email you log into Daily Drape with.
  3. Run:  py fix_admin_column.py
  4. Delete this file afterward — it's a one-time migration, not part
     of the running app.
"""
from sqlalchemy import text
from app import app, db

YOUR_EMAIL = "vishwajambu66@gmail.com"  # 👈 EDIT THIS to your real login email

with app.app_context():
    # Add the column if it's missing (safe to re-run, won't error if it already exists)
    db.session.execute(text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;"
    ))
    db.session.commit()
    print("✅ is_admin column present on users table.")

    # Promote your account
    result = db.session.execute(
        text("UPDATE users SET is_admin = TRUE WHERE email = :email"),
        {"email": YOUR_EMAIL}
    )
    db.session.commit()

    if result.rowcount == 0:
        print(f"⚠️  No user found with email '{YOUR_EMAIL}'. "
              f"Log in once via the app first, then re-run this script.")
    else:
        print(f"✅ {vishwajambu66@gmail.com} is now admin.")