import os
import sys

sys.path.append(os.getcwd())
from biobuddy.db import get_db

PAPERS_PATH = os.path.join("static", "papers")


def sync_papers():
    print(f"Starting database sync with folder: {PAPERS_PATH}")
    db = get_db()

    # 1. Get list of files in the database
    cursor = db.execute("SELECT filename FROM Papers")
    db_files = {row["filename"] for row in cursor.fetchall()}

    # 3. Get list of files on disk, only PDFs
    if not os.path.exists(PAPERS_PATH):
        print(f"Error: Directory {PAPERS_PATH} does not exist.")
        return

    disk_files = {f for f in os.listdir(PAPERS_PATH) if f.endswith(".pdf")}

    # 3. Determine files to add and remove
    files_to_add = disk_files - db_files
    files_to_remove = db_files - disk_files

    print(f"Analysis: {len(db_files)} in DB, {len(disk_files)} on disk.")
    print(f" -> To add: {len(files_to_add)}")
    print(f" -> To remove: {len(files_to_remove)}")

    # --- Stage 1: REMOVAL ---
    if files_to_remove:
        print("\nPruning removed files from Database...")
        for filename in files_to_remove:
            db.execute("DELETE FROM Papers WHERE filename = ?", (filename,))
            print(f" - Deleted: {filename}")

    # --- Stage 2: ADDITION ---
    if files_to_add:
        print("\nAdding new files to Database...")

        subjects_map = {}
        cursor = db.execute("SELECT name, id FROM Subjects")
        for row in cursor.fetchall():
            subjects_map[row["name"].lower()] = row["id"]

        added_count = 0
        for filename in files_to_add:
            try:
                name_parts = filename.replace(".pdf", "").split("_")

                if len(name_parts) < 5:
                    print(f" - Skipping invalid format: {filename}")
                    continue

                subj_str, year, level, type_str, num = name_parts[:5]

                subject_id = subjects_map.get(subj_str.lower())
                if not subject_id:
                    print(f" - Unknown subject: {subj_str} in {filename}")
                    continue

                if level not in ["HL", "SL"]:
                    print(f" - Invalid level: {level} in {filename}")
                    continue

                if type_str not in ["QP", "MS"]:
                    print(f" - Invalid type: {type_str} in {filename}")
                    continue

                if not num.isdigit():
                    print(f" - Invalid number: {num} in {filename}")
                    continue

                db.execute(
                    """
                    INSERT INTO Papers (subject_id, year, level, type, paper_number, filename)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (subject_id, int(year), level, type_str, int(num), filename),
                )
                print(f" + Added: {filename}")
                added_count += 1

            except Exception as e:
                print(f"Error processing {filename}: {e}")

        print(f"\nSuccessfully added {added_count} new papers.")
    else:
        print("\nNo new files to add.")

    db.close()
    print("\nSync complete.")


if __name__ == "__main__":
    sync_papers()
