from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)

app.config['SECRET_KEY'] = 'dev-key-change-later'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# class Students(db.Model):

#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(80), unique=True, nullable=False)
#     grade = db.Column(db.Integer, unique=False, nullable=False)

#     def __repr__(self):
#         return f"Student(name = {self.name}, grade = {self.grade})"

#three new classes!
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"{self.name} ({self.role})"


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    time = db.Column(db.String(80), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)

    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    teacher = db.relationship('User', backref='courses_taught')

    def __repr__(self):
        return self.name


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    grade = db.Column(db.Integer, nullable=True)

    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

    student = db.relationship('User', backref='enrollments')
    course = db.relationship('Course', backref='enrollments')

    def __repr__(self):
        return f"{self.student.name} in {self.course.name}"
    

# admin = Admin(app, name="ACME Admin")
# admin.add_view(ModelView(Students, db.session))

class UserAdmin(ModelView):
    column_list = ['name', 'username', 'role']
    column_searchable_list = ['name', 'username']
    column_filters = ['role']
    form_choices = {'role': [('student', 'Student'), ('teacher', 'Teacher'), ('admin', 'Admin')]}

class CourseAdmin(ModelView):
    column_list = ['name', 'teacher', 'time', 'capacity']
    column_searchable_list = ['name']

class EnrollmentAdmin(ModelView):
    column_list = ['student', 'course', 'grade']

admin = Admin(app, name="ACME Admin")
admin.add_view(UserAdmin(User, db.session))
admin.add_view(CourseAdmin(Course, db.session))
admin.add_view(EnrollmentAdmin(Enrollment, db.session))



with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST']) 
def login_page():

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'admin' and password == 'password':
            return render_template("index.html")
        elif username == 'admin1' and password == 'password123':
            return redirect('/admin/')
        elif username == 'teacher' and password == 'password':
            return redirect(url_for('teacher_home'))
        elif username == 'student' and password == 'password':
            return redirect(url_for('student_home'))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route('/index', methods=['GET', 'POST'])
def home():
    return render_template("index.html")


@app.route('/teacher', methods=['GET'])
def teacher_home():
    return render_template("prof_hp.html")


@app.route('/student', methods=['GET'])
def student_home():
    return render_template("student.html")

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
