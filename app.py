"""Flask routes for the Python Code Assistant."""

from __future__ import annotations

import os

from flask import Flask, render_template, request

from assistant.services import process_action

MAX_INPUT_CHARS = 20_000
VALID_ACTIONS = {"generate", "review", "fix", "error_explain", "program_explain"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024


@app.route("/", methods=["GET", "POST"])
def index():
    output = ""
    user_input = ""
    extra_input = "beginner"

    if request.method == "POST":
        user_input = request.form.get("user_input", "")
        action = request.form.get("action", "")
        extra_input = request.form.get("extra_input", "beginner")

        if not user_input.strip():
            output = "Enter a prompt or paste Python code before choosing an action."
        elif len(user_input) > MAX_INPUT_CHARS:
            output = f"Input is too long. Please keep it under {MAX_INPUT_CHARS:,} characters."
        elif action not in VALID_ACTIONS:
            output = "That action is not supported. Choose one of the buttons on the page."
        else:
            output = process_action(action, user_input, extra_input)

    return render_template(
        "index.html",
        output=output,
        user_input=user_input,
        extra_input=extra_input,
        max_input_chars=MAX_INPUT_CHARS,
    )


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
