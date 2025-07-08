from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin_user = User.query.filter_by(email="adminmu@weaboo.com").first()
    if not admin_user:
        admin_user = User(
            first_name="Admin",
            last_name="Weaboo",
            email="adminmu@weaboo.com",
            password=generate_password_hash("adminpassword123"),
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin user berhasil dibuat.")
    else:
        admin_user.is_admin = True
        db.session.commit()
        print("✅ Admin user sudah ada, hak admin diupdate.")
