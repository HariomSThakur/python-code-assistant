# Python Code Assistant

A small Flask app for exploring Python examples and understanding code structure. It uses Python's `ast` module for syntax-aware feedback and a collection of code examples for generation.

**This version does not use an AI model or an LLM.** The generator matches a prompt against supported keywords; an unfamiliar prompt gets a generic starter template. The review and explanation features use rules and Python's syntax tree. The project name is descriptive of its purpose, not a claim that the current implementation is model-powered.

## What it can do

- Generate example programs for common topics such as Fibonacci, a calculator, sorting, and simple games.
- Review submitted code for selected patterns, including long lines, bare `except`, mutable defaults, and basic structure.
- Explain Python syntax errors with the line and position reported by Python.
- Describe selected syntax-tree elements at beginner, intermediate, or advanced level.
- Suggest a missing colon when Python identifies a likely block header. It avoids trying to guess how arbitrary indentation should be repaired.
- Open code in OnlineGDB from the browser.

The review is a lightweight teaching aid, not a replacement for a linter, type checker, test suite, or experienced code review. It can miss problems and produce false positives.

## Run locally

You need Python 3.9 or newer and pip.

```powershell
git clone https://github.com/HariomSThakur/python-code-assistant.git
cd python-code-assistant
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in your browser. The Flask development server is intended for local use. Debug mode is off by default; set `FLASK_DEBUG=1` only while developing locally.

## Use the app

1. Enter a prompt for a supported example, or paste Python code.
2. Choose **Generate Code**, **Review**, **Auto-Fix**, **Explain Errors**, or **Explain Logic**.
3. For **Explain Logic**, choose the explanation level first.
4. Read the output and review any suggested code before using it.

The app does not execute submitted code on its Flask server. **Open in OnlineGDB** sends the code from the input box to the OnlineGDB website, which is a separate service. Do not send private or sensitive code there.

## Repository layout

```text
python-code-assistant/
├── app.py                 # Flask routes and request limits
├── assistant/
│   ├── analysis.py        # AST explanations, review, and narrow fixes
│   ├── generation.py      # Curated keyword-based examples
│   └── services.py        # Action dispatch
├── templates/
│   └── index.html         # Flask page template
├── static/
│   └── style.css          # Page styles
├── requirements.txt
└── README.md
```

## Current limitations

- Generation is keyword-based; it does not understand arbitrary requests like a language model would.
- Code review uses a small set of AST and text-based rules. It does not run the code, install packages, or check runtime behavior.
- Auto-Fix only makes a narrow missing-colon suggestion. Check the result before copying it into a project.
- The app has no authentication or persistent storage and is designed as a local learning demo.
