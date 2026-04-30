import hashlib
from database import init_db, get_db
from config import DEFAULT_ADMIN_USER, DEFAULT_ADMIN_PASS


def seed_data():
    conn = get_db()
    cur = conn.cursor()

    admin_pw = hashlib.md5(DEFAULT_ADMIN_PASS.encode()).hexdigest()
    editor_pw = hashlib.md5("editor123".encode()).hexdigest()

    cur.execute("""
        INSERT OR IGNORE INTO users (username, password, email, role)
        VALUES (?, ?, ?, ?)
    """, (DEFAULT_ADMIN_USER, admin_pw, "admin@example.com", "admin"))

    cur.execute("""
        INSERT OR IGNORE INTO users (username, password, email, role)
        VALUES (?, ?, ?, ?)
    """, ("editor", editor_pw, "editor@example.com", "editor"))

    cur.execute("""
        INSERT OR IGNORE INTO posts (title, content, excerpt, status, author_id, category)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("Welcome to WorldPress", "<p>This is your first post. Edit or delete it.</p>",
          "This is your first post.", "published", 1, "General"))

    cur.execute("""
        INSERT OR IGNORE INTO posts (title, content, excerpt, status, author_id, category)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("Getting Started Guide", "<p>Learn how to use WorldPress for your content needs.</p>",
          "Learn how to use WorldPress.", "draft", 2, "Tutorial"))

    cur.execute("""
        INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
    """, ("site_name", "WorldPress"))
    cur.execute("""
        INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
    """, ("site_description", "A WordPress-like CMS for learning"))
    cur.execute("""
        INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
    """, ("allow_registration", "false"))

    conn.commit()
    conn.close()
    print("Database initialized with seed data.")
    print(f"Admin login: {DEFAULT_ADMIN_USER} / {DEFAULT_ADMIN_PASS}")


if __name__ == "__main__":
    init_db()
    seed_data()
