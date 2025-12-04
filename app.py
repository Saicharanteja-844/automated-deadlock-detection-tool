# app.py - Main Flask application for Automated Deadlock Detection Tool
# Features: Web GUI, deadlock detection, input validation, resolution suggestions, DB for history.
# DB: SQLite table 'history' stores past runs (n, m, matrices as JSON, result, suggestions, timestamp).
# Run: python app.py (access at http://127.0.0.1:5000/)

from flask import Flask, request, render_template, redirect, url_for
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)

# Database setup
def init_db():
    connection = sqlite3.connect('deadlock_history.db')
    c = connection.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY,
                    n INTEGER,
                    m INTEGER,
                    allocation TEXT,
                    request TEXT,
                    available TEXT,
                    result TEXT,
                    suggestions TEXT,
                    safe_sequence TEXT,
                    timestamp TEXT
                )''')
    # Add safe_sequence column if it doesn't exist
    try:
        c.execute('ALTER TABLE history ADD COLUMN safe_sequence TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists
    connection.commit()
    connection.close()

init_db()

def validate_inputs(n, m, allocation, request, available):
    """
    Validates the input matrices and vectors for deadlock detection.

    Args:
        n (int): Number of processes.
        m (int): Number of resources.
        allocation (list of lists): Allocation matrix.
        request (list of lists): Request matrix.
        available (list): Available resources vector.

    Returns:
        tuple: (is_valid (bool), error_message (str))
    """
    if len(allocation) != n or any(len(row) != m for row in allocation):
        return False, "Allocation matrix must be n x m."
    if len(request) != n or any(len(row) != m for row in request):
        return False, "Request matrix must be n x m."
    if len(available) != m:
        return False, "Available vector must have m elements."
    for i in range(n):
        for j in range(m):
            if allocation[i][j] < 0 or request[i][j] < 0:
                return False, "Values must be non-negative."
    for val in available:
        if val < 0:
            return False, "Available values must be non-negative."
    return True, ""

def detect_deadlock(n, m, allocation, request, available):
    """
    Detects deadlocks using the Banker's Algorithm and computes the safe sequence.

    Args:
        n (int): Number of processes.
        m (int): Number of resources.
        allocation (list of lists): Current allocation matrix.
        request (list of lists): Request matrix.
        available (list): Available resources vector.

    Returns:
        tuple: (is_deadlock (bool), deadlocked_processes (list), message (str), safe_sequence (list))
    """
    work = available.copy()
    finish = [False] * n
    safe_sequence = []
    while True:
        found = False
        for i in range(n):
            if not finish[i] and all(request[i][j] <= work[j] for j in range(m)):
                work = [work[j] + allocation[i][j] for j in range(m)]
                finish[i] = True
                safe_sequence.append(i)
                found = True
        if not found:
            break
    deadlocked = [i for i in range(n) if not finish[i]]
    if deadlocked:
        return True, deadlocked, f"Deadlock detected in processes: {deadlocked}.", []
    return False, [], "No deadlock detected.", safe_sequence

def suggest_resolution(deadlocked, allocation, request):
    if not deadlocked:
        return "No action required."
    suggestions = [
        "Strategy 1: Terminate one or more deadlocked processes to break the circular wait.",
        "Strategy 2: Preempt resources from a process and rollback.",
    ]
    try:
        victim_candidate = min(deadlocked, key=lambda i: sum(allocation[i]))
        suggestions.append(f"Recommendation: Terminate Process P{victim_candidate} (holds fewest resources).")
    except ValueError:
        pass
    return "<br>".join(suggestions)

def save_to_db(n, m, allocation, request, available, result, suggestions, safe_sequence=None):
    """
    Saves the deadlock detection result to the database.

    Args:
        n (int): Number of processes.
        m (int): Number of resources.
        allocation (list of lists): Allocation matrix.
        request (list of lists): Request matrix.
        available (list): Available resources vector.
        result (str): Detection result message.
        suggestions (str): Resolution suggestions.
        safe_sequence (list): Safe sequence if no deadlock.
    """
    connection = sqlite3.connect('deadlock_history.db')
    c = connection.cursor()
    c.execute('INSERT INTO history (n, m, allocation, request, available, result, suggestions, safe_sequence, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
              (n, m, json.dumps(allocation), json.dumps(request),
                json.dumps(available), result, suggestions, json.dumps(safe_sequence) if safe_sequence else None,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    connection.commit()
    connection.close()

def get_history():
    """
    Retrieves the deadlock detection history from the database.

    Returns:
        list: List of history records with safe_sequence parsed from JSON.
    """
    connection = sqlite3.connect('deadlock_history.db')
    c = connection.cursor()
    c.execute('SELECT * FROM history ORDER BY id DESC')
    rows = c.fetchall()
    connection.close()
    # Parse safe_sequence from JSON
    parsed_rows = []
    for row in rows:
        parsed_row = list(row)
        if row[8]:  # safe_sequence column
            try:
                parsed_row[8] = json.loads(row[8])
            except json.JSONDecodeError:
                parsed_row[8] = None  # In case of invalid JSON
        parsed_rows.append(parsed_row)
    return parsed_rows

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Handles the main page for deadlock detection input and results.

    Returns:
        str: Rendered HTML template.
    """
    result = None
    suggestions = None
    safe_sequence = None
    if request.method == 'POST':
        try:
            n = int(request.form['n'])
            m = int(request.form['m'])
            allocation = [[int(request.form[f'alloc_{i}_{j}']) for j in range(m)] for i in range(n)]
            request_matrix = [[int(request.form[f'req_{i}_{j}']) for j in range(m)] for i in range(n)]
            available = [int(request.form[f'avail_{j}']) for j in range(m)]

            valid, error = validate_inputs(n, m, allocation, request_matrix, available)
            if not valid:
                result = f"Input error: {error}"
            else:
                is_deadlock, deadlocked, message, safe_seq = detect_deadlock(n, m, allocation, request_matrix, available)
                result = message
                safe_sequence = safe_seq if not is_deadlock else None
                suggestions = suggest_resolution(deadlocked, allocation, request_matrix)
                save_to_db(n, m, allocation, request_matrix, available, result, suggestions, safe_sequence)
        except ValueError:
            result = "Invalid input. Enter integers only."
    return render_template('index.html', result=result, suggestions=suggestions, safe_sequence=safe_sequence)

@app.route('/history')
def history():
    """
    Handles the history page displaying past deadlock detection results.

    Returns:
        str: Rendered HTML template.
    """
    history_data = get_history()
    return render_template('history.html', history=history_data)

if __name__ == '__main__':
    app.run(debug=True)
