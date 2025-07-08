from app import db, app, Event

with app.app_context():
    db.create_all()
    print("Database dan tabel berhasil dibuat.")

    event1 = Event(title="Anime Matsuri 2025", description="Festival Anime Terbesar", price=50000, stock=100)
    event2 = Event(title="Cosplay Competition", description="Lomba Cosplay Karakter Anime", price=30000, stock=50)
    db.session.add_all([event1, event2])
    db.session.commit()
    print("Event berhasil ditambahkan!")
