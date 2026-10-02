"""Dispatch supported web actions to the assistant helpers."""

from .analysis import auto_fix_code, explain_error, explain_program, review_code
from .generation import generate_code

def process_action(action, user_input, extra="", examples=None):
    if action == "generate":
        return generate_code(user_input, examples)
    elif action == "review":
        return review_code(user_input)
    elif action == "fix":
        return auto_fix_code(user_input)
    elif action == "error_explain":
        return explain_error(user_input)
    elif action == "program_explain":
        level = extra or "beginner"
        return explain_program(user_input, level)
    return "Invalid action selected."
