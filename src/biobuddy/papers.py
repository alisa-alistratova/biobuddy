"""
Module for retrieving papers based on subject and filters.
"""
from .db import Database


def get_papers(db: Database, subject_name, filters=None):
    """
    Retrieves papers based on subject and optional filters.
    filters: dict with keys 'year', 'level', 'type', 'paper_number'
    """
    # 1. Find subject ID
    subj_row = db.select_one(
        "SELECT id FROM Subjects WHERE name = ?", (subject_name.capitalize(),)
    )
    if not subj_row:
        return []

    subject_id = subj_row["id"]

    # 2. Basic query
    query = "SELECT * FROM Papers WHERE subject_id = ?"
    params = [subject_id]

    # 3. Dynamically add filters
    if filters:
        if filters.get("year"):
            query += " AND year = ?"
            params.append(filters["year"])

        if filters.get("level"):
            query += " AND level = ?"
            params.append(filters["level"])

        if filters.get("type"):
            query += " AND type = ?"
            params.append(filters["type"])

        if filters.get("paper_number"):
            query += " AND paper_number = ?"
            params.append(filters["paper_number"])

    # 4. Sort results
    query += " ORDER BY year DESC, level ASC, paper_number ASC"

    cursor = db.execute(query, tuple(params))
    return cursor.fetchall()


def get_unique_years(db: Database, subject_name):
    """Helper to populate the Year dropdown filter."""
    subj_row = db.select_one(
        "SELECT id FROM Subjects WHERE name = ?", (subject_name.capitalize(),)
    )
    if not subj_row:
        return []

    cursor = db.execute(
        "SELECT DISTINCT year FROM Papers WHERE subject_id = ? ORDER BY year DESC",
        (subj_row["id"],),
    )
    return [row["year"] for row in cursor.fetchall()]
