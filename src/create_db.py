import os
from biobuddy.db import Database
from biobuddy.user import create_user


# Configuration via Environment variables
DB_PATH = os.environ.get('DB_PATH', 'biobuddy.db')
PAPERS_PATH = os.environ.get('PAPERS_PATH', './static/papers')


SCHEMA_SQL = """
-- Database Schema for BioBuddy Application --

-- Users Table --
CREATE TABLE Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

-- Subjects Table --
CREATE TABLE Subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- Papers Table --
CREATE TABLE Papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    level TEXT NOT NULL CHECK(level IN ('HL', 'SL')),
    type TEXT NOT NULL CHECK(type IN ('QP', 'MS')), -- QP: Question Paper, MS: Mark Scheme
    paper_number INTEGER NOT NULL,  -- Paper Number (1, 2, 3)
    filename TEXT UNIQUE NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES Subjects (id)
);

-- Favorites Table --
CREATE TABLE Favorites (
    user_id INTEGER,
    paper_id INTEGER,
    PRIMARY KEY (user_id, paper_id),
    FOREIGN KEY (user_id) REFERENCES Users (id) ON DELETE CASCADE,
    FOREIGN KEY (paper_id) REFERENCES Papers (id) ON DELETE CASCADE
);

-- Flashcards Table --
CREATE TABLE Flashcards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    
    -- Current proficiency level:
    -- Box 1 = New/Hard (Review daily)
    -- Box 5 = Mastered (Review rarely)
    leitner_box INTEGER DEFAULT 1, 
    
    -- Spaced repetition logic:
    -- Stores the exact calculated timestamp when the card becomes visible again.
    -- If current_time < next_review_date, the query will hide this card.
    next_review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_reviewed TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES Users (id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES Subjects (id)
);

CREATE INDEX idx_cards_review ON Flashcards(user_id, next_review_date);

"""

def create_tables(db):
    db.execute_script(SCHEMA_SQL)
    print("Tables created successfully.")

    # """Creates the necessary tables and indexes."""
    # cursor = conn.cursor()
    #
    # # --- Table: Users ---
    # cursor.execute('''
    # CREATE TABLE IF NOT EXISTS Users (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     username TEXT UNIQUE NOT NULL,
    #     password_hash TEXT NOT NULL,
    #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    # );
    # ''')
    #
    # # --- Table: Subjects ---
    # # Good normalization practice: store names separately
    # cursor.execute('''
    # CREATE TABLE IF NOT EXISTS Subjects (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     name TEXT UNIQUE NOT NULL
    # );
    # ''')
    #
    # # --- Table: Papers (Resources) ---
    # cursor.execute('''
    # CREATE TABLE IF NOT EXISTS Papers (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     subject_id INTEGER NOT NULL,
    #     year INTEGER NOT NULL,
    #     level TEXT NOT NULL CHECK(level IN ('HL', 'SL')),
    #     type TEXT NOT NULL CHECK(type IN ('QP', 'MS')), -- QP: Question Paper, MS: Mark Scheme
    #     filename TEXT NOT NULL,
    #     FOREIGN KEY (subject_id) REFERENCES Subjects (id)
    # );
    # ''')
    #
    # # Index for fast filtering by subject and year (Use Case #7)
    # cursor.execute('CREATE INDEX IF NOT EXISTS idx_papers_filter ON Papers(subject_id, year);')
    #
    # # --- Table: Favorites ---
    # # Junction table for Many-to-Many relationship
    # cursor.execute('''
    # CREATE TABLE IF NOT EXISTS Favorites (
    #     user_id INTEGER,
    #     paper_id INTEGER,
    #     added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #     PRIMARY KEY (user_id, paper_id),
    #     FOREIGN KEY (user_id) REFERENCES Users (id) ON DELETE CASCADE,
    #     FOREIGN KEY (paper_id) REFERENCES Papers (id) ON DELETE CASCADE
    # );
    # ''')
    #
    # # --- Table: Flashcards (Crucial for HL Complexity) ---
    # cursor.execute('''
    # CREATE TABLE IF NOT EXISTS Flashcards (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     user_id INTEGER NOT NULL,
    #     subject_id INTEGER NOT NULL,
    #     question TEXT NOT NULL,
    #     answer TEXT NOT NULL,
    #     leitner_box INTEGER DEFAULT 1, -- Box 1 to 5
    #     next_review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #     last_reviewed TIMESTAMP,
    #     FOREIGN KEY (user_id) REFERENCES Users (id) ON DELETE CASCADE,
    #     FOREIGN KEY (subject_id) REFERENCES Subjects (id)
    # );
    # ''')
    #
    # # Index to quickly find cards due for review (Use Case #19)
    # cursor.execute('CREATE INDEX IF NOT EXISTS idx_cards_review ON Flashcards(user_id, next_review_date);')
    #
    # conn.commit()
    # print("Tables and Indexes created successfully.")


def scan_and_seed_papers(db: Database, papers_dir: str):
    """
    Scans 'static/papers/' and populates the DB automatically.
    Format: {Subject}_{Year}_{Level}_{Type}_{Number}.pdf
    """
    conn = db.connection
    cursor = db.cursor

    # Build subject name to ID map
    subjects_map = {}
    cursor.execute("SELECT name, id FROM Subjects")
    for row in cursor.fetchall():
        subjects_map[row[0].lower()] = row[1]  # {'biology': 1, 'chemistry': 2}

    files = os.listdir(papers_dir)
    count = 0

    for filename in files:
        if not filename.endswith(".pdf"):
            continue

        # Parse filename
        try:
            name_parts = filename.replace(".pdf", "").split("_")
            if len(name_parts) < 5:
                print(f"Skipping invalid format: {filename}")
                continue
            subj_str, year, level, type_str, num = name_parts[:5]

            # Checks
            subject_id = subjects_map.get(subj_str.lower())
            if not subject_id:
                print(f"Unknown subject in file: {filename}")
                continue
            if level not in ["HL", "SL"]:
                print(f"Invalid level in file: {filename}")
                continue
            if type_str not in ["QP", "MS"]:
                print(f"Invalid type in file: {filename}")
                continue
            if not num.isdigit():
                print(f"Invalid paper number in file: {filename}")
                continue

            # Insert if not exists
            cursor.execute(
                """
                SELECT id FROM Papers 
                WHERE filename = ?
                """,
                (filename,),
            )

            if not cursor.fetchone():
                cursor.execute(
                    """
                    INSERT INTO Papers (subject_id, year, level, type, paper_number, filename)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (subject_id, int(year), level, type_str, int(num), filename),
                )
                count += 1

        except ValueError:
            print(f"Error parsing: {filename}")

    conn.commit()
    print(f"Scanned folder. Added {count} new papers.")


def seed_initial_data(db):
    """Populates the database with initial required data."""
    create_user(db, "test", "123")

    for subject in ["Biology", "Chemistry"]:
        db.execute(
            "INSERT INTO Subjects (name) VALUES (?)",
            (subject,)
        )
    scan_and_seed_papers(db, PAPERS_PATH)


if __name__ == "__main__":
    print(f"Initializing database at: {DB_PATH}")
    try:
        db = Database(DB_PATH)
        create_tables(db)
        seed_initial_data(db)
        db.close()
        print("Database setup complete.")
    except Exception as e:
        print(f"Error initializing database: {e}")
