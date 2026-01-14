import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, g

from biobuddy.db import get_db
from biobuddy.user import create_user, authenticate_user
from biobuddy.papers import get_papers, get_unique_years
from biobuddy.favorites import toggle_favorite, get_user_favorites, get_favorite_ids
from biobuddy.flashcards import (
    get_user_flashcards, create_flashcard, delete_flashcard,
    get_subjects, get_card_by_id, update_flashcard
)
from biobuddy.study import get_due_cards, process_review

app = Flask(__name__)

# Secret key is needed for session security.
# In production, this should be a complex random string from ENV.
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key_123")
DB_PATH = os.environ.get("BIOBUDDY_DB_PATH", "biobuddy.db")

def get_db_connection():
    """
    Creates or retrieves a database connection for the current request.
    Uses Flask's `g` object to store the connection.
    """
    if 'db' not in g:
        g.db = get_db(DB_PATH)
    return g.db


@app.teardown_appcontext
def close_db(error):
    """Automatically close the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


# --- Routes ---
@app.route("/")
def index():
    user_id = session.get("user_id")
    username = None
    favorites = []

    if user_id:
        db = get_db_connection()
        user = db.select_one("SELECT username FROM Users WHERE id = ?", (user_id,))
        if user:
            username = user["username"]
            favorites = get_user_favorites(db, user_id)

    return render_template("index.html", user_id=user_id, username=username, favorites=favorites)


# -- Authentication Routes ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db_connection()
        if create_user(db, username, password):
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        else:
            flash("Username already exists.", "error")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db_connection()
        user_id = authenticate_user(db, username, password)

        if user_id is not None:
            session["user_id"] = user_id  # Save to session cookie
            flash("Welcome back!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# -- Paper Routes ---
@app.route("/papers/<subject>")
def resources(subject):
    db = get_db_connection()

    filters = {
        "year": request.args.get("year"),
        "level": request.args.get("level"),
        "type": request.args.get("type"),
        "paper_number": request.args.get("number"),
    }

    papers = get_papers(db, subject, filters)
    years = get_unique_years(db, subject)

    fav_ids = set()
    if "user_id" in session:
        fav_ids = get_favorite_ids(db, session["user_id"])

    return render_template(
        "papers.html",
        subject=subject.capitalize(),
        papers=papers,
        available_years=years,
        current_filters=filters,
        fav_ids=fav_ids,
    )


@app.route("/api/toggle_favorite", methods=["POST"])
def api_toggle_favorite():
    if "user_id" not in session:
        return {"error": "Unauthorized"}, 401

    data = request.json
    paper_id = data.get("paper_id")

    db = get_db_connection()
    is_active = toggle_favorite(db, session["user_id"], paper_id)

    return {"success": True, "is_active": is_active}


# -- Flashcard Routes ---
@app.route("/flashcards", methods=["GET", "POST"])
def flashcards():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    user_id = session["user_id"]

    # Handle Form Submission (Create New Card)
    if request.method == "POST":
        subject_id = request.form["subject_id"]
        question = request.form["question"]
        answer = request.form["answer"]

        create_flashcard(db, user_id, subject_id, question, answer)
        flash("Card added!", "success")
        return redirect(url_for("flashcards"))

    # Load data for the list view
    my_cards = get_user_flashcards(db, user_id)
    subjects = get_subjects(db)

    return render_template("flashcards.html", cards=my_cards, subjects=subjects)


@app.route("/flashcards/edit/<int:card_id>", methods=["GET", "POST"])
def edit_flashcard(card_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    user_id = session["user_id"]

    # 1. Fetch the card to ensure it exists and belongs to the user
    card = get_card_by_id(db, card_id, user_id)
    if not card:
        flash("Card not found or access denied.", "error")
        return redirect(url_for("flashcards"))

    # 2. Handle Form Submission (Update)
    if request.method == "POST":
        subject_id = request.form["subject_id"]
        question = request.form["question"]
        answer = request.form["answer"]

        update_flashcard(db, user_id, card_id, subject_id, question, answer)
        flash("Card updated successfully.", "success")
        return redirect(url_for("flashcards"))

    # 3. GET request: Render the edit form with pre-filled data
    subjects = get_subjects(db)
    return render_template("edit_flashcard.html", card=card, subjects=subjects)


@app.route("/flashcards/delete/<int:card_id>", methods=["POST"])
def delete_card_route(card_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    delete_flashcard(db, session["user_id"], card_id)

    flash("Card deleted.", "info")
    return redirect(url_for("flashcards"))


# -- Study Routes ---
@app.route("/study")
def study_session():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    user_id = session["user_id"]

    # Get all due cards
    due_cards = get_due_cards(db, user_id)

    if not due_cards:
        # If no cards are due, show a "Good Job" page
        return render_template("study_complete.html")

    # Pick the first card in the queue
    current_card = due_cards[0]
    remaining_count = len(due_cards)

    return render_template("study.html", card=current_card, count=remaining_count)


@app.route("/study/submit/<int:card_id>/<rating>")
def study_submit(card_id, rating):
    """
    Handles the button click (Hard/Medium/Easy).
    Redirects back to /study to load the next card.
    """
    if "user_id" not in session:
        return redirect(url_for("login"))

    if rating not in ["hard", "medium", "easy"]:
        return redirect(url_for("study_session"))

    db = get_db_connection()
    process_review(db, session["user_id"], card_id, rating)

    return redirect(url_for("study_session"))


if __name__ == "__main__":
    app.run(debug=True, port=25001)
