"""
The favorites (likes) management module.
"""
from .db import Database

def toggle_favorite(db: Database, user_id, paper_id):
    """
    If there is a like - removes it. If not - adds it.
    Returns True if added (active), False if removed.
    """
    # 1. Check if already in favorites
    existing = db.select_one(
        "SELECT 1 FROM Favorites WHERE user_id = ? AND paper_id = ?", 
        (user_id, paper_id)
    )
    
    if existing:
        # Remove
        db.execute(
            "DELETE FROM Favorites WHERE user_id = ? AND paper_id = ?", 
            (user_id, paper_id)
        )
        return False
    else:
        # Add
        db.execute(
            "INSERT INTO Favorites (user_id, paper_id) VALUES (?, ?)", 
            (user_id, paper_id)
        )
        return True


def get_user_favorites(db: Database, user_id):
    """
    Returns papers favorited by the user, ordered by most recently added.
    """
    query = """
        SELECT p.*, s.name as subject_name
        FROM Papers p
        JOIN Favorites f ON p.id = f.paper_id
        JOIN Subjects s ON p.subject_id = s.id
        WHERE f.user_id = ?
    """
    cursor = db.execute(query, (user_id,))
    return cursor.fetchall()


def get_favorite_ids(db: Database, user_id):
    """
    Returns a set of paper IDs favorited by the user for quick lookup "if paper.id in favorites".
    """
    cursor = db.execute("SELECT paper_id FROM Favorites WHERE user_id = ?", (user_id,))
    return {row['paper_id'] for row in cursor.fetchall()}
