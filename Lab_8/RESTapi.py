from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)

app.config['SECRET_KEY'] = 'dev-key-change-later'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

class Students(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    grade = db.Column(db.Integer, unique=False, nullable=False)

    def __repr__(self):
        return f"Student(name = {self.name}, grade = {self.grade})"

admin = Admin(app, name="ACME Admin")
admin.add_view(ModelView(Students, db.session))

with app.app_context():
    db.create_all()

@app.route('/') 
def home():
    return render_template("index.html")

@app.route('/login')
def login_page():
    return render_template("login.html")

# GET (READ) all students
@app.route('/students', methods=["GET"])
def get_students():

    students = Students.query.all()

    result = {}
    for student in students:
        result[student.name] = student.grade

    return jsonify(result)

@app.route('/students/<name>', methods=["GET"])
def get_student(name):

    student = Students.query.filter_by(name=name).first()

    if student:
        return jsonify({
            "name": student.name,
            "grade": student.grade
        })
    return jsonify({"error": "Student not found"}), 404

@app.route('/students', methods=["POST"])
def add_student():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    name = data.get("name")
    grade = data.get("grade")

    if not name or grade is None:
        return jsonify({"error": "Missing name or grade"}), 400

    existing = Students.query.filter_by(name=name).first()
    if existing:
        return jsonify({"error": "Student already exists"}), 400
    
    new_student = Students(name=name, grade=grade)

    db.session.add(new_student)
    db.session.commit()

    return jsonify({
        "name": name,
        "grade": grade
    })

# PUT (UPDATE) update grade
@app.route('/students/<name>', methods=["PUT"])
def update_student(name):

    student = Students.query.filter_by(name=name).first()

    #student not found
    if not student:
        return jsonify({"error": "Student not found"}), 404
    
    data = request.get_json()
    student.grade = data.get("grade")

    db.session.commit()

    return jsonify({
        "name": student.name,
        "grade": student.grade
    })

# DELETE student
@app.route('/students/<name>', methods=["DELETE"])
def delete_student(name):
    
    student = Students.query.filter_by(name=name).first()

    if not student:
        return jsonify({"error": "Student not found"}), 404
    
    db.session.delete(student)
    db.session.commit()

    return jsonify({"message": f"{name} deleted"})

# starts flask server, use py RESTapi.py to run
if __name__ == '__main__':
    app.run()
