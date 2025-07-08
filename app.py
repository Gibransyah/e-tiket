from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os
import qrcode
from functools import wraps
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'safed2c3211e5f96caa9b072572b2f1f5'

# Konfigurasi login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'

# Konfigurasi database (PostgreSQL Railway / SQLite lokal)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///local.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Model Event
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

# Model User
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Paid, Failed
    payment_method = db.Column(db.String(50))  # Contoh: QRIS, Transfer, Virtual Account
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='transactions')
    event = db.relationship('Event', backref='transactions')


# User loader
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Route Beranda
@app.route("/")
def home():
    events = Event.query.all()
    return render_template("home.html", events=events)

# Route Detail Event
@app.route("/event/<int:event_id>")
def detail_event(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template("detail_event.html", event=event)

# Route Checkout Tiket
@app.route("/checkout/<int:event_id>", methods=["GET", "POST"])
@login_required
def checkout(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == "POST":
        if event.stock > 0:
            transaction = Transaction(
                user_id=current_user.id,
                event_id=event.id,
                amount=event.price,
                status='Pending',
                payment_method='QRIS'  # default, nanti bisa user pilih
            )
            db.session.add(transaction)
            db.session.commit()
            return redirect(url_for('payment', transaction_id=transaction.id))
        else:
            flash("Maaf, tiket sudah habis.")
            return redirect(url_for('home'))
    return render_template("checkout.html", event=event)

@app.route('/payment/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def payment(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    if transaction.user_id != current_user.id:
        flash("Anda tidak memiliki akses ke transaksi ini.")
        return redirect(url_for('home'))

    if request.method == 'POST':
        # Jika manual, user klik konfirmasi pembayaran
        transaction.status = 'Paid'
        db.session.commit()
        flash("Pembayaran telah dikonfirmasi. Tiket Anda aktif.")
        return redirect(url_for('transactions'))

    return render_template('payment.html', transaction=transaction)

@app.route('/transactions')
@login_required
def transactions():
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    return render_template('transactions.html', transactions=transactions)


# Route Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Email atau kata sandi salah, coba lagi.')
    return render_template('login.html')

# Route Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Kata sandi tidak cocok, coba lagi.')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        if User.query.filter_by(email=email).first():
            flash('Email sudah terdaftar, silakan gunakan email lain.')
            return redirect(url_for('register'))

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Pendaftaran berhasil, silakan login.')
        return redirect(url_for('login'))
    return render_template('register.html')

# Route Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/events")
def events():
    events = Event.query.all()
    return render_template("events.html", events=events)

@app.route("/tentang")
def tentang():
    return render_template("tentang.html")

@app.route("/kontak")
def kontak():
    return render_template("kontak.html")

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Anda tidak memiliki izin untuk mengakses halaman ini.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Halaman Dashboard Admin - List Event
@app.route('/admin/events')
@admin_required
def admin_events():
    events = Event.query.all()
    return render_template('admin_events.html', events=events)

# Tambah Event
@app.route('/admin/events/add', methods=['GET', 'POST'])
@admin_required
def add_event():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = request.form['price']
        stock = request.form['stock']

        new_event = Event(
            title=title,
            description=description,
            price=int(price),
            stock=int(stock)
        )
        db.session.add(new_event)
        db.session.commit()
        flash("Event berhasil ditambahkan!", "success")
        return redirect(url_for('admin_events'))

    return render_template('admin_event_form.html', action='Tambah')

# Edit Event
@app.route('/admin/events/edit/<int:event_id>', methods=['GET', 'POST'])
@admin_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == 'POST':
        event.title = request.form['title']
        event.description = request.form['description']
        event.price = int(request.form['price'])
        event.stock = int(request.form['stock'])

        db.session.commit()
        flash("Event berhasil diperbarui!", "success")
        return redirect(url_for('admin_events'))

    return render_template('admin_event_form.html', action='Edit', event=event)

# Hapus Event
@app.route('/admin/events/delete/<int:event_id>', methods=['POST'])
@admin_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash("Event berhasil dihapus!", "success")
    return redirect(url_for('admin_events'))

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

