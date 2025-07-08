from app import app, db, Event

with app.app_context():
    event1 = Event(
        title="Festival Anime Jakarta 2025",
        description="Event cosplay, merchandise, dan pertunjukan musik anime terbesar di Jakarta.",
        price=150000,
        stock=100
    )

    event2 = Event(
        title="Workshop Manga bersama Sensei",
        description="Belajar menggambar manga dari mangaka profesional dengan tips langsung.",
        price=200000,
        stock=50
    )

    event3 = Event(
        title="Konser J-Pop Night",
        description="Nikmati konser J-Pop dengan artis Jepang favoritmu secara langsung.",
        price=250000,
        stock=80
    )

    db.session.add_all([event1, event2, event3])
    db.session.commit()
    print("✅ Contoh event berhasil ditambahkan ke database.")
