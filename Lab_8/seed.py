from RESTapi import app, db, User, Course, Enrollment

with app.app_context():
    db.drop_all()
    db.create_all()

    # Teachers
    ralph = User(username="rjenkins", password="password", name="Ralph Jenkins", role="teacher")
    susan = User(username="swalker", password="password", name="Susan Walker", role="teacher")
    ammon = User(username="ahepworth", password="password", name="Ammon Hepworth", role="teacher")

    # Students
    jose = User(username="jsantos", password="password", name="Jose Santos", role="student")
    betty = User(username="bbrown", password="password", name="Betty Brown", role="student")
    john = User(username="jstuart", password="password", name="John Stuart", role="student")
    li = User(username="lcheng", password="password", name="Li Cheng", role="student")
    nancy = User(username="nlittle", password="password", name="Nancy Little", role="student")
    mindy = User(username="mnorris", password="password", name="Mindy Norris", role="student")
    aditya = User(username="aranganath", password="password", name="Aditya Ranganath", role="student")
    yi = User(username="ychen", password="password", name="Yi Wen Chen", role="student")

    # Admin
    admin_user = User(username="admin", password="admin", name="Admin", role="admin")

    db.session.add_all([ralph, susan, ammon, jose, betty, john, li, nancy, mindy, aditya, yi, admin_user])
    db.session.commit()

    # Courses
    math101 = Course(name="Math 101", time="MWF 10:00-10:50 AM", capacity=8, teacher_id=ralph.id)
    phys121 = Course(name="Physics 121", time="TR 11:00-11:50 AM", capacity=10, teacher_id=susan.id)
    cs106 = Course(name="CS 106", time="MWF 2:00-2:50 PM", capacity=10, teacher_id=ammon.id)
    cs162 = Course(name="CS 162", time="TR 3:00-3:50 PM", capacity=4, teacher_id=ammon.id)

    db.session.add_all([math101, phys121, cs106, cs162])
    db.session.commit()

    # Enrollments
    enrollments = [
        Enrollment(student_id=jose.id, course_id=math101.id, grade=92),
        Enrollment(student_id=betty.id, course_id=math101.id, grade=65),
        Enrollment(student_id=john.id, course_id=math101.id, grade=86),
        Enrollment(student_id=li.id, course_id=math101.id, grade=77),
        Enrollment(student_id=nancy.id, course_id=phys121.id, grade=53),
        Enrollment(student_id=li.id, course_id=phys121.id, grade=85),
        Enrollment(student_id=mindy.id, course_id=phys121.id, grade=94),
        Enrollment(student_id=john.id, course_id=phys121.id, grade=91),
        Enrollment(student_id=betty.id, course_id=phys121.id, grade=88),
        Enrollment(student_id=aditya.id, course_id=cs106.id, grade=93),
        Enrollment(student_id=yi.id, course_id=cs106.id, grade=85),
        Enrollment(student_id=nancy.id, course_id=cs106.id, grade=57),
        Enrollment(student_id=mindy.id, course_id=cs106.id, grade=68),
        Enrollment(student_id=aditya.id, course_id=cs162.id, grade=99),
        Enrollment(student_id=nancy.id, course_id=cs162.id, grade=87),
        Enrollment(student_id=yi.id, course_id=cs162.id, grade=92),
        Enrollment(student_id=john.id, course_id=cs162.id, grade=67),
    ]

    db.session.add_all(enrollments)
    db.session.commit()
    print("Database seeded!")