from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import flask_login
from flask import Flask, render_template, request, jsonify, url_for, redirect, flash
import stripe
from flask_login import LoginManager, UserMixin, login_user, login_required

login_manager = LoginManager()

app = Flask(__name__)
app.secret_key = "12345"
app.config['SECRET_KEY'] = 'secret-key-goes-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config["STRIPE_PUBLIC_KEY"] = "pk_test_51Kj0OSBQMouEZApwt2fB5dDsTEmVNG99dRrrc8feRGTwpyyvJPnWVJUqGTmcbLLEGjID8ssGs7r4ubTUpvRlxXpj00MCbmQLYO"
app.config["STRIPE_SECRET_KEY"] = "sk_test_51Kj0OSBQMouEZApwsVxdZoyQdhH8pc0U3Emqw3iHv4Xd9a94YrnZlMD7vCCwm1splMhLeXkuBAArR2OeDJ8SQEv0006uXlDv03"
stripe.api_key = app.config["STRIPE_SECRET_KEY"]
db = SQLAlchemy(app)
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


class Users(db.Model, UserMixin):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)


class Products(db.Model):
    __tablename__ = "Products"
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    img = db.Column(db.String(120))
    description = db.Column(db.String(120))
    size = db.Column(db.String(20))


@app.route("/registration", methods=["GET", "POST"])
def registration():
    if request.method == "POST":
        new_user = Users(username= request.form.get("name"),
                         email= request.form.get("email"),
                         password= request.form.get("pass"))
        db.session.add(new_user)
        db.session.commit()
        user = Users.query.filter_by(username=new_user.username).first()
        flash("Logged in successfully")
        login_user(user)
        print(new_user.username)
        return redirect(url_for("home_page", username=new_user.username))

    return render_template("registration.html")


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = Users.query.filter_by(username=request.form.get("username")).first()
        if user:
            login_user(user)
            return redirect(url_for("home_page", username=request.form.get("username")))
    return render_template("login.html")


@app.route('/create-checkout-session', methods=["GET", "POST"])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    'price': 'price_1KlxZIBQMouEZApwoQRLvYIo',
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=url_for("thank", _external=True),
            cancel_url=url_for("home_page", _external=True),
        )
    except Exception as e:
        return str(e)
    return redirect(checkout_session.url, code=303)


CART = []

@app.route("/home", methods=["GET", "POST"])
@login_required
def home_page():
    if request.args.get("product"):
        CART.append(request.args.get("product"))

    products = stripe.Product.list()["data"]
    return render_template("index.html", username=request.args.get("username"), products=products, cart_id=len(CART))


@app.route("/cart", methods=["GET", "POST"])
def cart():
    product = Products.query.filter_by(id=request.args.get('product_id')).first()
    return render_template('cart.html', product=product, cart_id=len(CART))


@app.route("/checkout_page", methods=["GET", "POST"])
def checkout_page():
    return render_template('checkout.html')


@app.route("/Thank You", methods=["GET", "POST"])
def thank():
    return render_template("thank.html")


if __name__ == "__main__":
    app.run(debug=True)