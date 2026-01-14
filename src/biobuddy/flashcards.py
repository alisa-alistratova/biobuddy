"""
Module for managing flashcards: create, read, update, delete.
"""
from .db import Database


def get_user_flashcards(db: Database, user_id):
    """
    Retrieves all flashcards for a specific user.
    Joins with Subjects table to get friendly names.
    Orders by ID descending (newest first).
    """
    query = '''
        SELECT f.*, s.name as subject_name 
        FROM Flashcards f
        JOIN Subjects s ON f.subject_id = s.id
        WHERE f.user_id = ?
        ORDER BY f.id DESC
    '''
    cursor = db.execute(query, (user_id,))
    return cursor.fetchall()


def get_card_by_id(db: Database, card_id, user_id):
    """
    Fetches a single card.
    Crucial for the 'Edit' page to pre-fill the form.
    Includes a user_id check to prevent accessing other people's cards.
    """
    query = "SELECT * FROM Flashcards WHERE id = ? AND user_id = ?"
    return db.select_one(query, (card_id, user_id))


def create_flashcard(db: Database, user_id, subject_id, question, answer):
    """
    Creates a new card.
    Default state: Leitner Box 1, Review Date = Now.
    """
    db.execute('''
        INSERT INTO Flashcards (user_id, subject_id, question, answer, leitner_box, next_review_date)
        VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
    ''', (user_id, subject_id, question, answer))


def update_flashcard(db: Database, user_id, card_id, subject_id, question, answer):
    """
    Updates an existing card.
    Security: Always checks user_id to ensure ownership.
    """
    db.execute('''
        UPDATE Flashcards 
        SET subject_id = ?, question = ?, answer = ?
        WHERE id = ? AND user_id = ?
    ''', (subject_id, question, answer, card_id, user_id))


def delete_flashcard(db: Database, user_id, card_id):
    """
    Permanently removes a card.
    """
    db.execute('''
        DELETE FROM Flashcards 
        WHERE id = ? AND user_id = ?
    ''', (card_id, user_id))


def get_subjects(db: Database):
    """
    Helper to populate dropdown menus (Biology, Chemistry).
    """
    cursor = db.execute("SELECT * FROM Subjects")
    return cursor.fetchall()
