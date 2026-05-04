from flask import Flask, render_template, request, redirect, url_for, session


app = Flask(__name__)
app.secret_key = "wordle-login-secret"


@app.route("/", methods=["GET", "POST"])
def login():
	error = None

	if request.method == "POST":
		username = request.form.get("username", "").strip()
		password = request.form.get("password", "")

		if username == "player" and password == "guess":
			session["logged_in"] = True
			session["username"] = username
			return redirect(url_for("lobby"))

		error = "Invalid username or password."

	return render_template("login.html", error=error)


@app.route("/lobby")
def lobby():
	if not session.get("logged_in"):
		return redirect(url_for("login"))

	return render_template("lobby.html", username=session.get("username", "Player"))


@app.route("/logout")
def logout():
	session.clear()
	return redirect(url_for("login"))


if __name__ == "__main__":
	app.run(debug=True)
