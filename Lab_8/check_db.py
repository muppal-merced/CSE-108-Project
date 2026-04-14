# check_db.py
from RESTapi import db, app, Students  # import the Flask app

# Run inside the app context
with app.app_context():
    students = Students.query.all()
    if not students:
        print("No students in the database.")
    else:
        for s in students:
            print(f"id={s.id}, name={s.name}, grade={s.grade}")