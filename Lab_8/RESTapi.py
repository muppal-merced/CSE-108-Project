from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)

app.config['SECRET_KEY'] = 'dev-key-change-later'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)


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


def get_current_teacher():
    """Return the logged-in teacher or None if the session is invalid."""
    if session.get('role') != 'teacher':
        return None

    teacher_user = None

    if session.get('user_id') is not None:
        teacher_user = User.query.filter_by(id=session['user_id'], role='teacher').first()

    if teacher_user is None and session.get('username'):
        teacher_user = User.query.filter_by(username=session['username'], role='teacher').first()

    return teacher_user


def get_current_student():
    """Return the logged-in student or None if the session is invalid."""
    if session.get('role') != 'student':
        return None

    student_user = None

    if session.get('user_id') is not None:
        student_user = User.query.filter_by(id=session['user_id'], role='student').first()

    if student_user is None and session.get('username'):
        student_user = User.query.filter_by(username=session['username'], role='student').first()

    return student_user
    


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

        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            # save who's logged in for other pages to use
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role

            # redirect based on role
            if user.role == 'admin':
                return redirect('/admin/')
            elif user.role == 'teacher':
                return redirect(url_for('teacher_home'))
            elif user.role == 'student':
                return redirect(url_for('student_home'))

        if username == 'admin' and password == 'password':
            session['username'] = username
            session['role'] = 'admin'
            return render_template("index.html")
        elif username == 'admin1' and password == 'password123':
            session['username'] = username
            session['role'] = 'admin'
            return redirect('/admin/')
        elif username == 'teacher' and password == 'password':
            session['username'] = username
            session['role'] = 'teacher'
            return redirect(url_for('teacher_home'))
        elif username == 'student' and password == 'password':
            session['username'] = username
            session['role'] = 'student'
            return redirect(url_for('student_home'))
        else:
            return render_template("login.html", error="Invalid credentials")
        
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/index', methods=['GET', 'POST'])
def home():
    return render_template("index.html")


@app.route('/teacher', methods=['GET'])
def teacher_home():
    teacher_user = get_current_teacher()

    if teacher_user is None:
        session.clear()
        return redirect(url_for('login_page'))

    rows = []
    courses = Course.query.filter_by(teacher_id=teacher_user.id).order_by(Course.name).all()

    for course in courses:
        if not course.enrollments:
            rows.append({
                "enrollment_id": None,
                "course_name": course.name,
                "teacher_name": teacher_user.name,
                "student_name": "No students enrolled",
                "grade": "-"
            })
            continue

        for enrollment in course.enrollments:
            rows.append({
                "enrollment_id": enrollment.id,
                "course_name": course.name,
                "teacher_name": teacher_user.name,
                "student_name": enrollment.student.name,
                "grade": enrollment.grade
            })

    return render_template("prof_hp.html", rows=rows)


@app.route('/teacher/grades/<int:enrollment_id>', methods=['POST'])
def update_teacher_grade(enrollment_id):
    teacher_user = get_current_teacher()

    if teacher_user is None:
        session.clear()
        return redirect(url_for('login_page'))

    enrollment = (
        Enrollment.query
        .join(Course)
        .filter(
            Enrollment.id == enrollment_id,
            Course.teacher_id == teacher_user.id
        )
        .first()
    )

    if enrollment is None:
        return jsonify({"error": "Enrollment not found"}), 404

    grade_value = request.form.get('grade', '').strip()

    if grade_value == '':
        enrollment.grade = None
    else:
        try:
            enrollment.grade = int(grade_value)
        except ValueError:
            return jsonify({"error": "Grade must be a whole number"}), 400

    db.session.commit()
    return redirect(url_for('teacher_home'))


@app.route('/student', methods=['GET'])
def student_home():
    student_user = get_current_student()

    if student_user is None:
        session.clear()
        return redirect(url_for('login_page'))

    courses = Course.query.order_by(Course.name).all()

    my_courses = []
    all_courses = []

    for course in courses:
        enrolled_count = len(course.enrollments)
        student_enrollment = next((e for e in course.enrollments if e.student_id == student_user.id), None)

        all_courses.append({
            "id": course.id,
            "name": course.name,
            "teacher": course.teacher.name,
            "time": course.time,
            "enrolled": enrolled_count,
            "capacity": course.capacity,
            "is_enrolled": student_enrollment is not None,
            "is_full": enrolled_count >= course.capacity
        })

        if student_enrollment is not None:
            my_courses.append({
                "id": course.id,
                "name": course.name,
                "teacher": course.teacher.name,
                "time": course.time,
                "enrolled": enrolled_count,
                "capacity": course.capacity,
                "grade": student_enrollment.grade
            })

    return render_template(
        "student.html",
        student_name=student_user.name if student_user else "Student",
        my_courses=my_courses,
        all_courses=all_courses
    )


@app.route('/student/enroll/<int:course_id>', methods=['POST'])
def enroll_course(course_id):
    student_user = get_current_student()

    if student_user is None:
        session.clear()
        return redirect(url_for('login_page'))

    course = Course.query.get(course_id)
    if course is None:
        return redirect(url_for('student_home'))

    existing = Enrollment.query.filter_by(student_id=student_user.id, course_id=course.id).first()
    if existing is not None:
        return redirect(url_for('student_home'))

    enrolled_count = Enrollment.query.filter_by(course_id=course.id).count()
    if enrolled_count >= course.capacity:
        return redirect(url_for('student_home'))

    enrollment = Enrollment(student_id=student_user.id, course_id=course.id, grade=None)
    db.session.add(enrollment)
    db.session.commit()

    return redirect(url_for('student_home'))


@app.route('/student/drop/<int:course_id>', methods=['POST'])
def drop_course(course_id):
    student_user = get_current_student()

    if student_user is None:
        session.clear()
        return redirect(url_for('login_page'))

    enrollment = Enrollment.query.filter_by(student_id=student_user.id, course_id=course_id).first()
    if enrollment is None:
        return redirect(url_for('student_home'))

    db.session.delete(enrollment)
    db.session.commit()

    return redirect(url_for('student_home'))

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
