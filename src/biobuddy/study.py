"""
Module for handling spaced repetition reviews using the Leitner system.
"""
from .db import Database

from datetime import datetime, timedelta

# Leitner System Intervals (Days)
# Box 1: Daily, Box 2: 3 days, Box 3: Week, etc.
INTERVALS = {1: 1, 2: 3, 3: 7, 4: 14, 5: 30}


def get_due_cards(db: Database, user_id):
    """
    Fetches cards where next_review_date is in the past or today.
    Ordered by priority (Review date).
    """
    query = """
        SELECT f.*, s.name as subject_name 
        FROM Flashcards f
        JOIN Subjects s ON f.subject_id = s.id
        WHERE f.user_id = ? 
        AND f.next_review_date <= datetime('now', 'localtime')
        ORDER BY f.next_review_date ASC
    """
    return db.execute(query, (user_id,)).fetchall()


def process_review(db: Database, user_id, card_id, rating):
    """
    Updates the card's Box and Next Review Date based on user rating.
    rating: 'hard' (reset), 'medium' (stay), 'easy' (advance)
    """
    # 1. Get current card state
    card = db.select_one(
        "SELECT leitner_box FROM Flashcards WHERE id=? AND user_id=?",
        (card_id, user_id),
    )
    if not card:
        return

    current_box = card["leitner_box"]
    new_box = current_box

    # 2. Apply Leitner Logic
    if rating == "easy":
        # Promote: Move to next box (max 5)
        new_box = min(5, current_box + 1)
    elif rating == "medium":
        # Stagnate: Stay in current box (or demote if strictly punitive, but 'stay' is friendlier)
        new_box = current_box
    elif rating == "hard":
        # Demote: Reset to Box 1 (Need to relearn)
        new_box = 1

    # 3. Calculate time delay
    days_delay = INTERVALS.get(new_box, 1)

    # If it was hard, we might want to review it sooner (e.g. 10 minutes),
    # but for this MVP, we set it to 'tomorrow' or 'same day' logic.
    # Let's add the timedelta to current time.
    if rating == "hard":
        # If hard, review again very soon (e.g., 0 days = remains 'due' effectively, or 1 day)
        # Let's set to 0 days (effectively immediately/tomorrow depending on your logic)
        # For simplicity in MVP: Reset to Box 1 means review tomorrow.
        days_delay = 0

    next_date = datetime.now() + timedelta(days=days_delay)

    # 4. Update DB
    db.execute(
        """
        UPDATE Flashcards 
        SET leitner_box = ?, next_review_date = ?
        WHERE id = ? AND user_id = ?
    """,
        (new_box, next_date, card_id, user_id),
    )

