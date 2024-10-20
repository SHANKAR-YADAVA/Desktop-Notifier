from app import app, db

# Create application context
with app.app_context():
    db.create_all()  # Create all tables
    print("Database initialized successfully.")
