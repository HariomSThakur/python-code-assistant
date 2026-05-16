# 🐍 Python Code Assistant

> A web-based Python code assistant that generates, reviews, fixes, and explains code — with one-click online execution and file saving.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Web%20App-black?logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

## 📖 Table of Contents

- [About](#-about)
- [Features](#-features)
- [Screenshots](#-screenshots)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [How It Works](#-how-it-works)
- [Code Templates](#-code-templates)
- [Contributing](#-contributing)
- [License](#-license)

---

## 📌 About

**Python Code Assistant** is a lightweight Flask web application that acts as a smart coding companion for Python learners and developers. It requires **no external AI API** — all logic runs locally using Python's built-in `ast` module and a rich library of hand-crafted code templates.

Paste a prompt or existing code, click a button, and instantly get generated code, a review, an auto-fix, an error explanation, or a line-by-line logic breakdown.

---

## ✨ Features

| Feature | Description |
|---|---|
| ⚡ **Generate Code** | Converts plain-English prompts into ready-to-run Python programs |
| 🔍 **Code Review** | Analyzes code for syntax issues, style problems, and bad practices |
| 🔧 **Auto-Fix** | Automatically corrects syntax errors, indentation, and missing imports |
| ❌ **Explain Errors** | Explains syntax errors in plain English with line numbers and fix tips |
| 🧠 **Explain Logic** | Line-by-line AST-based breakdown at Beginner / Intermediate / Advanced level |
| ▶ **Run Online** | Opens your code in OnlineGDB's Python compiler in one click |
| 💾 **Save Output** | Downloads the AI response as a `.py` file instantly |
| 🎨 **Glassmorphism UI** | Sleek dark interface with gradient accents and smooth animations |

---

## 🖼️ Screenshots

> _Add screenshots here after running the app._

| Home Screen | Generated Code | Error Explanation |
|---|---|---|
| _(screenshot)_ | _(screenshot)_ | _(screenshot)_ |

---

## ⚙️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/python-code-assistant.git
cd python-code-assistant
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install flask
```

> That's it — no external APIs, no heavy ML libraries required.

### 4. Run the app
```bash
python app.py
```

Open your browser and go to: **`http://127.0.0.1:5000`**

---

## 🚀 Usage

### Generate Code
Type a plain-English prompt and click **Generate Code**:
```
bubble sort
fibonacci series
calculator
tic tac toe
hangman
```
The assistant recognizes 40+ program types by keyword and returns clean, runnable Python code.

---

### Review Code
Paste any Python code and click **Review** to get:
- Syntax error detection
- Style and practice suggestions
- Import analysis
- Structural feedback

---

### Auto-Fix
Paste broken Python code and click **Auto-Fix**. The assistant will:
- Fix common syntax errors (missing colons, unclosed brackets, etc.)
- Correct inconsistent indentation
- Add missing imports automatically

---

### Explain Errors
Paste code with a syntax error and click **Explain Errors** to get:
- A human-readable description of the error
- The exact line and character position (`^ here`)
- Common causes and how to fix them

---

### Explain Logic
Paste code and click **Explain Logic** for a line-by-line AST breakdown at three levels:

| Level | Description |
|---|---|
| **Beginner** | Simple analogies — "storing something in a box", "repeating some code" |
| **Intermediate** | Actual variable names, conditions, and function signatures |
| **Advanced** | Execution model, scope rules, complexity notes, edge case tips |

---

### Run Online
Click **▶ Run Online** to open your code directly in [OnlineGDB](https://www.onlinegdb.com/online_python_compiler) — no copy-paste needed.

---

### Save Output
Click **💾 Save** to download the current AI response as `code_assistant_output.py`.

---

## 📁 Project Structure

```
python-code-assistant/
│
├── app.py                  # Flask backend — all logic lives here
│
├── templates/
│   └── index.html          # Jinja2 frontend template
│
├── static/
│   └── style.css           # Glassmorphism dark UI styles
│
└── README.md               # This file
```

> **Note:** Place `index.html` inside a `templates/` folder and `style.css` inside a `static/` folder for Flask to find them correctly.

---

## 🔍 How It Works

```
User Input (prompt or code)
        │
        ▼
   Action Selected
        │
   ┌────┴──────────────────────────────────────┐
   │                                           │
generate              review / fix / explain / error_explain
   │                                           │
Keyword               Python ast module parses the code
matching              │
   │                  ├── SyntaxError → explain_error()
   ▼                  ├── AST walk   → explain_program()
40+ templates         ├── Style scan → review_code()
   │                  └── Auto patch → auto_fix_code()
   └──────────────────────────┐
                              ▼
                    Flask renders index.html
                    with output in <pre> block
```

### Key modules used

| Module | Purpose |
|--------|---------|
| `flask` | Web server and routing |
| `ast` | Parse and analyze Python code structure |
| `re` | Pattern matching for keyword detection and fixes |
| `textwrap` | Text formatting for clean output |
| `traceback` | Safe error capturing |

---

## 📚 Code Templates

The generator recognizes 40+ common Python program types by keyword. A sample:

| Keyword(s) | Program Generated |
|---|---|
| `hello world` | Classic Hello World |
| `fizzbuzz`, `fizz buzz` | FizzBuzz (1–100) |
| `calculator` | Basic arithmetic calculator |
| `fibonacci` | Fibonacci series |
| `bubble sort` | Bubble sort algorithm |
| `binary search` | Binary search implementation |
| `hangman` | Hangman game |
| `tic tac toe` | 2-player Tic Tac Toe |
| `guess number` | Number guessing game |
| `todo` | To-do list manager |
| `qr code` | QR code generator |
| `alarm clock` | Simple alarm |
| `stack`, `queue`, `linked list` | Data structure implementations |
| `merge sort`, `quick sort` | Sorting algorithms |
| `caesar cipher` | Encryption / decryption |
| `web scraper` | Basic requests + BeautifulSoup |
| `email slicer` | Parse email username & domain |
| `pig latin` | Pig Latin translator |
| `magic 8 ball` | Random answer game |
| `mad libs` | Story fill-in game |
| `dice roller` | Multi-sided dice simulator |
| `story generator` | Random story builder |
| ...and more | — |

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature`
3. Make your changes and commit: `git commit -m "Add: your feature"`
4. Push to your fork: `git push origin feature/your-feature`
5. Open a Pull Request

### Ideas for contributions
- Add more code generation templates
- Integrate a real LLM API (Gemini, Groq, Ollama) for arbitrary prompts
- Add syntax highlighting to the output block (Prism.js / highlight.js)
- Add a "Copy to Clipboard" button for the output
- Dark/light theme toggle

---

## 📄 License

This project is licensed under the **MIT License**.  
Feel free to use, modify, and distribute it.

---

<p align="center">Made with ❤️ by Hariom Thakur</p>
