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
                    timestamp TEXT
                )''')
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
    Detects deadlocks using the Banker's Algorithm.

    Args:
        n (int): Number of processes.
        m (int): Number of resources.
        allocation (list of lists): Current allocation matrix.
        request (list of lists): Request matrix.
        available (list): Available resources vector.

    Returns:
        tuple: (is_deadlock (bool), deadlocked_processes (list), message (str))
    """
    work = available.copy()
    finish = [False] * n
    while True:
        found = False
        for i in range(n):
            if not finish[i] and all(request[i][j] <= work[j] for j in range(m)):
                work = [work[j] + allocation[i][j] for j in range(m)]
                finish[i] = True
                found = True
        if not found:
            break
    deadlocked = [i for i in range(n) if not finish[i]]
    if deadlocked:
        return True, deadlocked, f"Deadlock detected in processes: {deadlocked}."
    return False, [], "No deadlock detected."

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

def save_to_db(n, m, allocation, request, available, result, suggestions):
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
    """
    connection = sqlite3.connect('deadlock_history.db')
    c = connection.cursor()
    c.execute('INSERT INTO history (n, m, allocation, request, available, result, suggestions, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
              (n, m, json.dumps(allocation), json.dumps(request),
                json.dumps(available), result, suggestions,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    connection.commit()
    connection.close()

def get_history():
    """
    Retrieves the deadlock detection history from the database.

    Returns:
        list: List of history records.
    """
    connection = sqlite3.connect('deadlock_history.db')
    c = connection.cursor()
    c.execute('SELECT * FROM history ORDER BY id DESC')
    rows = c.fetchall()
    connection.close()
    return rows

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Handles the main page for deadlock detection input and results.

    Returns:
        str: Rendered HTML template.
    """
    result = None
    suggestions = None
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
                is_deadlock, deadlocked, message = detect_deadlock(n, m, allocation, request_matrix, available)
                result = message
                suggestions = suggest_resolution(deadlocked, allocation, request_matrix)
                save_to_db(n, m, allocation, request_matrix, available, result, suggestions)
        except ValueError:
            result = "Invalid input. Enter integers only."
    return render_template('index.html', result=result, suggestions=suggestions)

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
