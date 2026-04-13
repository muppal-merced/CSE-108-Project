from RESTapi import app, db, Students
    #app: flask application
    #db: SQLAlchemy instance (managing the database)
        #in RESTapi.py:
            #app = Flask(__name__)
            #db = SQLAlchemy(app)

#creates a Flask application context
    #creates database and puts it in instance folder
with app.app_context():
    db.create_all()

    #test student
    if not Students.query.first():
        student = Students(name="Bob", grade=100)
        db.session.add(student)
        db.session.commit()
