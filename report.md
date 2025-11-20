# Project Report: Automated Deadlock Detection Tool

## 1. Project Overview
The Automated Deadlock Detection Tool is a web-based application designed to detect potential deadlocks in operating system processes. It implements the Banker's algorithm to analyze resource allocation and request matrices, identifying circular wait conditions that could lead to deadlocks. The tool provides a user-friendly interface for inputting process and resource data, displays detection results, and offers resolution suggestions. The project aims to assist in understanding and preventing deadlocks in multi-process systems, with expected outcomes including accurate deadlock detection, historical tracking of analyses, and educational insights into resource management.

## 2. Module-Wise Breakdown
The project is divided into three main modules:

- **Backend Module**: Handles the core logic for deadlock detection, input validation, and database operations. It processes user inputs, runs the Banker's algorithm, and stores results in a SQLite database.
- **Frontend Module**: Provides the web interface for user interaction, including dynamic form generation for matrices and display of results. It uses HTML, CSS, and JavaScript for a responsive and intuitive user experience.
- **Database Module**: Manages persistent storage of deadlock detection history, allowing users to view past analyses and track changes over time.

## 3. Functionalities
- **Backend Module**:
  - Input validation for processes (n), resources (m), allocation matrix, request matrix, and available resources.
  - Deadlock detection using the Banker's algorithm, identifying deadlocked processes.
  - Generation of resolution suggestions, such as terminating processes or reallocating resources.
  - Database integration for saving and retrieving history.

- **Frontend Module**:
  - Dynamic generation of input forms based on user-specified n and m values.
  - Display of detection results and suggestions.
  - Navigation between home and history pages.
  - Responsive design with CSS styling and JavaScript for interactivity.

- **Database Module**:
  - Storage of detection runs with timestamps.
  - Retrieval and display of historical data in a tabular format.

## 4. Technology Used
- **Programming Languages**:
  - Python (for backend logic)
  - HTML, CSS, JavaScript (for frontend)

- **Libraries and Tools**:
  - Flask (web framework for Python)
  - SQLite (database for history storage)
  - Jinja2 (templating engine for HTML)

- **Other Tools**: GitHub for version control

## 5. Flow Diagram
```
User Input (n, m, matrices) --> Frontend Form Submission --> Backend Validation --> Deadlock Detection (Banker's Algorithm) --> Result Display --> Save to Database --> History Page Access
```

## 6. Revision Tracking on GitHub
- **Repository Name**: automated-deadlock-detection-tool
- **GitHub Link**: https://github.com/Saicharanteja-844/automated-deadlock-detection-tool.git

## 7. Conclusion and Future Scope
The Automated Deadlock Detection Tool successfully implements deadlock detection using the Banker's algorithm in a web-based interface, providing an educational and practical tool for OS concepts. Future enhancements could include real-time process monitoring integration, advanced algorithms like resource allocation graphs, and multi-user support with authentication.

## 8. References
- Operating System Concepts by Abraham Silberschatz
- Flask Documentation
- SQLite Documentation

## Appendix

### A. AI-Generated Project Elaboration/Breakdown Report
**Project Overview**: The project's goal is to develop a tool for automatic deadlock detection in system processes, focusing on analyzing dependencies and resource allocation to identify circular waits. Expected outcomes include a functional web app that detects deadlocks and suggests resolutions. Scope covers input handling, algorithm implementation, and result visualization.

**Module-Wise Breakdown**:
- Backend: Core processing and algorithm execution.
- Frontend: User interface and interaction.
- Database: Data persistence and history.

**Functionalities**:
- Backend: Validation, detection, suggestions.
- Frontend: Form generation, result display.
- Database: History storage and retrieval.

**Technology Recommendations**: Python with Flask for backend, HTML/CSS/JS for frontend, SQLite for database.

**Execution Plan**:
1. Set up Flask app structure.
2. Implement Banker's algorithm.
3. Create HTML templates and JS for dynamic forms.
4. Add database integration.
5. Test and deploy.

### B. Problem Statement
Develop a tool that automatically detects potential deadlocks in system processes. The tool should analyze process dependencies and resource allocation to identify circular wait conditions and suggest resolution strategies.

### C. Solution/Code
#### app.py
```python
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
        return "No resolution needed."
    suggestions = [
        f"1. Terminate deadlocked processes (e.g., {deadlocked[0]}).",
        "2. Preempt and reallocate resources.",
        "3. Rollback to safe state."
    ]
    min_alloc = min(sum(allocation[i]) for i in deadlocked)
    for i in deadlocked:
        if sum(allocation[i]) == min_alloc:
            suggestions.append(f"4. Recommended: Terminate process {i}.")
            break
    return " ".join(suggestions)

def save_to_db(n, m, allocation, request, available, result, suggestions):
    connection = sqlite3.connect('deadlock_history.db')
    c = connection.cursor()
    c.execute('INSERT INTO history (n, m, allocation, request, available, result, suggestions, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
              (n, m, json.dumps(allocation), json.dumps(request), json.dumps(available), result, suggestions, datetime.now().isoformat()))
    connection.commit()
    connection.close()

def get_history():
    connection = sqlite3.connect('deadlock_history.db')
    c = connection.cursor()
    c.execute('SELECT id, n, m, result, timestamp FROM history ORDER BY timestamp DESC')
    rows = c.fetchall()
    connection.close()
    return rows

@app.route('/', methods=['GET', 'POST'])
def index():
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
    history_data = get_history()
    return render_template('history.html', history=history_data)

if __name__ == '__main__':
    app.run(debug=True)
```

#### templates/index.html
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Automated Deadlock Detection Tool</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
</head>
<body>
    <header>
        <h1>Automated Deadlock Detection Tool</h1>
        <nav>
            <a href="/">Home</a> | <a href="/history">View History</a>
        </nav>
    </header>
    <main>
        <p>Enter the number of processes (n) and resources (m), then fill the matrices for easy deadlock detection.</p>
        <form method="post" id="detection-form">
            <label>Number of Processes (n): <input type="number" name="n" id="n" required></label><br>
            <label>Number of Resources (m): <input type="number" name="m" id="m" required></label><br>
            
            <h3>Allocation Matrix (n x m)</h3>
            <div id="allocation-matrix" class="matrix"></div>
            
            <h3>Request Matrix (n x m)</h3>
            <div id="request-matrix" class="matrix"></div>
            
            <h3>Available Resources (m values)</h3>
            <div id="available-resources" class="resources"></div>
            
            <button type="submit">Detect Deadlock</button>
        </form>
        
        {% if result %}
        <div class="result">
            <h3>Result:</h3>
            <p>{{ result }}</p>
            {% if suggestions %}
            <h3>Suggestions:</h3>
            <p>{{ suggestions }}</p>
            {% endif %}
        </div>
        {% endif %}
    </main>
    <script src="{{ url_for('static', filename='script.js') }}"></script>
</body>
</html>
```

#### static/script.js
```javascript
function generateMatrix(containerId, rows, cols, prefix) {
    const container = document.getElementById(containerId);
    container.innerHTML = ''; // Clear previous content
    for (let i = 0; i < rows; i++) {
        for (let j = 0; j < cols; j++) {
            const input = document.createElement('input');
            input.type = 'number';
            input.name = `${prefix}_${i}_${j}`;
            input.required = true;
            input.min = 0; // Ensure non-negative values
            container.appendChild(input);
        }
        container.appendChild(document.createElement('br')); // New line for each row
    }
}

function generateResources(containerId, cols, prefix) {
    const container = document.getElementById(containerId);
    container.innerHTML = ''; // Clear previous content
    for (let j = 0; j < cols; j++) {
        const input = document.createElement('input');
        input.type = 'number';
        input.name = `${prefix}_${j}`;
        input.required = true;
        input.min = 0; // Ensure non-negative values
        container.appendChild(input);
    }
    container.appendChild(document.createElement('br')); // New line after inputs
}

document.getElementById('n').addEventListener('input', function() {
    const n = parseInt(this.value) || 0; // Default to 0 if invalid
    const m = parseInt(document.getElementById('m').value) || 0; // Default to 0 if invalid
    if (n > 0 && m > 0) {
        generateMatrix('allocation-matrix', n, m, 'alloc');
        generateMatrix('request-matrix', n, m, 'req');
        generateResources('available-resources', m, 'avail');
    } else {
        // Clear matrices if inputs are invalid
        document.getElementById('allocation-matrix').innerHTML = '';
        document.getElementById('request-matrix').innerHTML = '';
        document.getElementById('available-resources').innerHTML = '';
    }
});

document.getElementById('m').addEventListener('input', function() {
    const n = parseInt(document.getElementById('n').value) || 0; // Default to 0 if invalid
    const m = parseInt(this.value) || 0; // Default to 0 if invalid
    if (n > 0 && m > 0) {
        generateMatrix('allocation-matrix', n, m, 'alloc');
        generateMatrix('request-matrix', n, m, 'req');
        generateResources('available-resources', m, 'avail');
    } else {
        // Clear matrices if inputs are invalid
        document.getElementById('allocation-matrix').innerHTML = '';
        document.getElementById('request-matrix').innerHTML = '';
        document.getElementById('available-resources').innerHTML = '';
    }
});
```

#### static/styles.css
```css
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 20px;
    background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 100%);
    min-height: 100vh;
    color: #333;
}

header {
    background: linear-gradient(135deg, #1976d2 0%, #42a5f5 100%);
    color: white;
    padding: 20px;
    text-align: center;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

nav a {
    color: #e3f2fd;
    margin: 0 15px;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.3s ease;
}

nav a:hover {
    color: #ffffff;
    text-decoration: underline;
}

main {
    max-width: 900px;
    margin: 20px auto;
    background: rgba(255, 255, 255, 0.95);
    padding: 30px;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.18);
}

form {
    margin-bottom: 20px;
}

input,
button {
    margin: 5px;
    padding: 10px 15px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 16px;
    transition: all 0.3s ease;
}

input:focus {
    outline: none;
    border-color: #42a5f5;
    box-shadow: 0 0 5px rgba(66, 165, 245, 0.5);
}

.matrix,
.resources {
    display: flex;
    flex-direction: column;
}

.row {
    display: flex;
    align-items: center;
}

.row label {
    margin-right: 10px;
}

button {
    background: linear-gradient(135deg, #4CAF50 0%, #66BB6A 100%);
    color: white;
    cursor: pointer;
    border: none;
    font-weight: 600;
    transition: all 0.3s ease;
}

button:hover {
    background: linear-gradient(135deg, #45a049 0%, #4CAF50 100%);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
}

.result {
    background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
    padding: 20px;
    border: 1px solid #b3d9ff;
    border-radius: 8px;
    margin-top: 20px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

table {
    width: 100%;
    border-collapse: collapse;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

th,
td {
    border: 1px solid #ddd;
    padding: 12px;
    text-align: left;
}

th {
    background: linear-gradient(135deg, #1976d2 0%, #42a5f5 100%);
    color: white;
    font-weight: 600;
}

tbody tr:nth-child(even) {
    background-color: #f9f9f9;
}

tbody tr:hover {
    background-color: #e3f2fd;
    transition: background-color 0.3s ease;
}
```

#### templates/history.html
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deadlock Detection History</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
</head>
<body>
    <header>
        <h1>Deadlock Detection History</h1>
        <nav>
            <a href="/">Home</a> | <a href="/history">View History</a>
        </nav>
    </header>
    <main>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Processes (n)</th>
                    <th>Resources (m)</th>
                    <th>Result</th>
                    <th>Timestamp</th>
                </tr>
            </thead>
            <tbody>
                {% for item in history %}
                <tr>
                    <td>{{ item[0] }}</td>
                    <td>{{ item[1] }}</td>
                    <td>{{ item[2] }}</td>
                    <td>{{ item[3] }}</td>
                    <td>{{ item[4] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </main>
</body>
</html>
