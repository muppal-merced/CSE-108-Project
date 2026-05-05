# handles: login, signup, logout

from flask import render_template, request, redirect, url_for, session
from app.models import User
from app.extensions import db

def register_auth_routes(app):

    @app.route("/", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                session["logged_in"] = True
                session["user_id"] = user.id
                session["username"] = user.username
                return redirect(url_for("lobby"))
            else:
                error = "Invalid username or password."

        return render_template("login.html", error=error)

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        error = None
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            if not username or not password:
                error = "Username and password are required."
            elif User.query.filter_by(username=username).first():
                error = "Username already exists."
            else:
                user = User(username=username)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                session["logged_in"] = True
                session["user_id"] = user.id
                session["username"] = user.username
                return redirect(url_for("lobby"))

        return render_template("signup.html", error=error)


    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))