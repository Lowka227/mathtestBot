import sqlite3
import random
from config import DATABASE

class DB_Manager:
    def __init__(self):
        self.database = DATABASE
        self.create_tables()

    def create_tables(self):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id TEXT UNIQUE NOT NULL,
                name TEXT,
                score INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Problems (
                problem_id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_text TEXT NOT NULL,
                correct_answer TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id INTEGER,
                problem_id INTEGER,
                answer_text TEXT,
                is_correct INTEGER DEFAULT 0,
                UNIQUE(participant_id, problem_id),
                FOREIGN KEY (participant_id) REFERENCES participants(id),
                FOREIGN KEY (problem_id) REFERENCES Problems(problem_id)
            )
        ''')

        conn.commit()
        conn.close()

    def add_problem(self, text, answer):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Problems (problem_text, correct_answer) VALUES (?, ?)", (text, answer))
        conn.commit()
        conn.close()

    def add_participant(self, telegram_id, name):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO participants (telegram_id, name, score) VALUES (?, ?, 0)", (str(telegram_id), name))
        conn.commit()
        conn.close()

    def get_participant_id(self, telegram_id):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM participants WHERE telegram_id = ?", (str(telegram_id),))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def get_random_unused_problem(self, user_id):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute("SELECT problem_id, problem_text FROM Problems")
        all_problems = cursor.fetchall()
        if not all_problems:
            return None
        cursor.execute("SELECT problem_id FROM answers WHERE participant_id = ?", (user_id,))
        answered = {row[0] for row in cursor.fetchall()}
        unused = [p for p in all_problems if p[0] not in answered]
        
        if not unused:
            return None
        return random.choice(unused)
    
    def del_table_problems(self):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Problems")
        conn.commit()
        conn.close()

    def check_answer(self, problem_id, user_answer):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute("SELECT correct_answer FROM Problems WHERE problem_id = ?", (problem_id,))
        correct = cursor.fetchone()
        conn.close()
        return correct and correct[0].strip().lower() == user_answer.strip().lower()

    def save_answer(self, telegram_id, problem_id, answer_text, is_correct):
        participant_id = self.get_participant_id(telegram_id)
        if not participant_id:
            return

        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO answers (participant_id, problem_id, answer_text, is_correct)
        VALUES (?, ?, ?, ?)
    """, (participant_id, problem_id, answer_text, 1 if is_correct else 0))
    
        if is_correct:
            cursor.execute("UPDATE participants SET score = score + 1 WHERE id = ?", (participant_id,))
            conn.commit()
            conn.close()

    def get_rating(self, limit=10):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, score FROM participants
            WHERE score > 0
            ORDER BY score DESC, name
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows
    def check_all_answers(self, participant_id):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM answers WHERE participant_id = ? AND is_correct = 1", (participant_id,))
        correct_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM answers WHERE participant_id = ?", (participant_id,))
        total_count = cursor.fetchone()[0]
        conn.close()
        return correct_count == total_count

if __name__ == "__main__":
    manager = DB_Manager()
    
