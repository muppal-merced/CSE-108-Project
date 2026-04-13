from flask import Flask
from flask_admin import Admin


app = Flask(__name__)
# set optional bootswatch theme
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
admin = Admin(app, name='microblog', template_mode='bootstrap3')
# Add administrative views here
app.run()

from flask_sqlalchemy import SQLAlchemy

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///example.sqlite"
db = SQLAlchemy(app)

class User(db.Model):
id = db.Column(db.Integer, primary_key=True)
username = db.Column(db.String, unique=True, nullable=False)
email = db.Column(db.String, unique=True, nullable=False)


from flask_admin.contrib.sqla import ModelView

app.secret_key = 'super secret key’ # Add this to avoid an error

# Flask and Flask-SQLAlchemy initialization here
admin = Admin(app, name='microblog', template_mode='bootstrap3’)
admin.add_view(ModelView(User, db.session))

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
app.secret_key = 'keep it secret, keep it safe' # Add this to avoid an error
