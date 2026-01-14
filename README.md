# BioBuddy

**BioBuddy** is a specialized web-based educational platform designed for IB (International Baccalaureate) students to streamline their revision of Biology and Chemistry. It combines a structured past paper resource catalog with an intelligent flashcard system powered by Spaced Repetition logic.

**Live Demo:** [http://biobuddy.pythonanywhere.com/](http://biobuddy.pythonanywhere.com/)

---

## Key Features

* **Intelligent Flashcards:** Implements the **Leitner System** (Spaced Repetition) to optimize memory retention based on user proficiency levels.
* **Resource Catalog:** A dynamically filtered repository of past papers (Biology/Chemistry) with automatic file-system-to-database synchronization.
* **User Dashboard:** Personal profiles where students can manage their flashcard decks and "star" important resources for quick access.
* **Secure Authentication:** User data protection using PBKDF2 salted hashing.
* **Responsive UI:** A clean, focused interface built with **Pico.css** for distraction-free studying.
* **Interactive Study Mode:** 3D animated flashcards with self-assessment ratings (Hard/Medium/Easy).

---

## Technology Stack

* **Backend:** Python 3.11+, Flask (Web Framework)
* **Database:** SQLite3 (Relational Database)
* **Frontend:** HTML5, Modern CSS (Pico.css), Vanilla JavaScript (AJAX/Fetch API)
* **Deployment:** PythonAnywhere

---

## Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/alisa-alistratova/biobuddy.git](https://github.com/alisa-alistratova/biobuddy.git)
    cd biobuddy
    ```

2.  **Set up a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize the database:**
    ```bash
    python src/create_db.py
    ```

5.  **Run the application:**
    ```bash
    python src/app.py
    ```

---

## Project Structure

* `app.py` — Main Flask application and routing.
* `biobuddy/` — Core logic modules (Auth, Flashcards, Study algorithm, DB management).
* `static/` — CSS, JavaScript, and PDF resource storage.
* `templates/` — Jinja2 HTML templates.
* `update_papers.py` — Utility script for synchronizing the PDF folder with the database.

---

## License

This project was developed as part of a Computer Science Internal Assessment (IA) for the IB Diploma Programme.
