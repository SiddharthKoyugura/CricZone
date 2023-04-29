from flask import *
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor, CKEditorField
from flask_gravatar import Gravatar
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, Email
import pandas as pd

app = Flask(__name__)

app.config["SECRET_KEY"] = "ThisIsOurPlanetLet'sSaveIt"

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
ckeditor = CKEditor(app)
Bootstrap(app)
db = SQLAlchemy(app)



class User(UserMixin, db.Model):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)
    email = db.Column(db.Text, unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)

db.create_all()

# Forms
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

queries = []
query_data = pd.read_csv("data.csv", error_bad_lines=False, header=None, index_col=0, squeeze = True)
query_data =query_data.drop_duplicates()
query_data = query_data.to_dict()


@app.route("/home")
@login_required
def home():
    return render_template("index.html", current_user=current_user)

@app.route("/table", methods=["GET", "POST"])
@login_required
def table():
    if request.method == "POST":
        query = request.form.get("query").title()
        try:
            queries.append({
                "s.no":len(queries)+3,
                "query":query,
                "result":query_data[query]
                })
        except:
            flash("AI couldn't find the query")
        return redirect("table")
    return render_template("tables-general.html", current_user=current_user, queries=queries)

@app.route("/chart")
@login_required
def chart():
    return render_template("charts.html", current_user=current_user)

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", current_user=current_user)

@app.route("/blog")
@login_required
def blog():
    try:
        posts = BlogPost.query.all()
    except:
        posts = None
    return render_template("blogs.html", current_user=current_user, all_posts=posts)

@app.route("/add-blog", methods=["GET", "POST"])
@login_required
def add_blog():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('blog'))
    return render_template("add-blog.html", form=form)

@app.route("/post/<int:post_id>")
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    return render_template("post.html", post=requested_post)

# User-Authentication

@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")

        if User.query.filter_by(email=email).first():
            flash("User already registered, Please login instead!")
            return redirect(url_for('login'))

        name, password = request.form.get("name"), request.form.get("password")
        new_user = User(
            name = name,
            email = email,
            password = password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        if user:
            password = request.form.get("password")
            if user.password == password:
                login_user(user)
                return redirect(url_for("home"))
 
            flash("Invalid password")
            return redirect(url_for("login"))

        flash("User not registered with email!")
        return redirect(url_for("login"))
    
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="localhost", port=3000, debug=True)