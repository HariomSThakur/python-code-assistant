"""AST-backed explanations and heuristic code review helpers."""

import ast
import io
import re
import tokenize

class VariableVisitor(ast.NodeVisitor):
    def __init__(self):
        self.assigned = set()
        self.used = set()
        self.functions = 0
        self.loops = 0
        self.conditionals = 0
        self.imports = set()
        self.potential_missing_imports = set()

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.assigned.add(target.id)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used.add(node.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.functions += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.loops += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.loops += 1
        self.generic_visit(node)

    def visit_If(self, node):
        self.conditionals += 1
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.imports.add(node.module.split('.')[0])
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name):
            module_name = node.value.id
            if module_name not in self.imports and module_name not in self.assigned:
                self.potential_missing_imports.add(module_name)
        self.generic_visit(node)

def review_code(code):
    issues = []
    summary = []
    try:
        tree = ast.parse(code)
        visitor = VariableVisitor()
        visitor.visit(tree)

        unused = visitor.assigned - visitor.used
        if unused:
            issues.append(f"Unused variables: {', '.join(unused)}. These are assigned but never used, which might indicate dead code or a bug.")

        if visitor.potential_missing_imports:
            issues.append(f"Potential missing imports: {', '.join(visitor.potential_missing_imports)}. These look like module names used without import statements.")

        summary.append(f"Code structure summary:")
        summary.append(f"- Total lines: {len(code.splitlines())}")
        summary.append(f"- Functions defined: {visitor.functions}")
        summary.append(f"- Loops (for/while): {visitor.loops}")
        summary.append(f"- Conditionals (if/elif/else): {visitor.conditionals}")
        summary.append(f"- Imports: {', '.join(visitor.imports) if visitor.imports else 'None'}")

        # AST-based: check if any FunctionDef has a Return node
        has_return = any(
            isinstance(node, ast.Return)
            for node in ast.walk(tree)
        )
        if visitor.functions > 0 and not has_return:
            issues.append("Functions defined but no explicit 'return' statements found. This is fine if functions only print/mutate, but add returns where values are needed.")

        if 'while True' in code and 'break' not in code:
            issues.append("Potential infinite loop: 'while True' without a 'break' statement.")

        # Check for bare 'except:' (catches everything including KeyboardInterrupt)
        for i, line in enumerate(code.splitlines(), 1):
            stripped = line.strip()
            if stripped == 'except:':
                issues.append(f"Line {i}: Bare 'except:' catches all exceptions including system exits. Use 'except Exception:' or specify the exception type.")
            # Check for very long lines
            if len(line) > 120:
                issues.append(f"Line {i}: Very long line ({len(line)} chars). Consider breaking it up for readability.")

        # Check for missing if __name__ == '__main__': guard when functions exist
        if visitor.functions > 0 and '__name__' not in code:
            issues.append("Tip: Consider wrapping top-level code in a main() function and adding a __name__ guard so it is safe to import.")

        # Check for mutable default arguments (common Python gotcha)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        issues.append(f"Line {node.lineno}: Function '{node.name}' uses a mutable default argument (list/dict/set). This is a common Python gotcha — use None as default and initialise inside the function instead.")

    except SyntaxError as e:
        issues.append(f"Syntax Error: {str(e)}. Check the line mentioned for issues like missing parentheses, colons, or incorrect indentation.")

    result = "Code Review Result:\n"
    if issues:
        result += "\n".join(issues) + "\n\n"
    else:
        result += "No major issues detected. Code is syntactically valid.\n\n"
    
    if summary:
        result += "\n".join(summary)
    
    return result

_BLOCK_HEADER = re.compile(
    r"^(?:if|elif|else|for|while|def|class|try|except|finally|with|async\s+(?:def|for|with))\b"
)


def _split_trailing_comment(line):
    try:
        for token in tokenize.generate_tokens(io.StringIO(line).readline):
            if token.type == tokenize.COMMENT:
                return line[: token.start[1]].rstrip(), line[token.start[1] :]
    except (tokenize.TokenError, IndentationError):
        pass
    return line.rstrip(), ""


def fix_missing_colon(code):
    """Add a colon only when the parser points to a likely block header."""
    try:
        ast.parse(code)
    except SyntaxError as error:
        line_number = error.lineno
        if line_number is None:
            return code
    else:
        return code

    lines = code.splitlines(keepends=True)
    line_index = line_number - 1
    if not 0 <= line_index < len(lines):
        return code

    original = lines[line_index]
    ending = ""
    content = original
    if content.endswith("\r\n"):
        content, ending = content[:-2], "\r\n"
    elif content.endswith(("\n", "\r")):
        content, ending = content[:-1], content[-1]

    header, comment = _split_trailing_comment(content)
    header_text = header.lstrip()
    if not _BLOCK_HEADER.match(header_text) or header.rstrip().endswith(":"):
        return code

    comment_suffix = (" " if comment else "") + comment
    lines[line_index] = header.rstrip() + ":" + comment_suffix + ending
    return "".join(lines)


def auto_fix_code(code):
    """Offer a narrow syntax suggestion; avoid rewriting indentation heuristically."""
    fixed = fix_missing_colon(code)
    if fixed != code:
        changes = "added a colon to the block header flagged by Python"
    else:
        changes = "no safe automatic change identified"

    try:
        ast.parse(fixed)
    except SyntaxError as error:
        syntax_status = f"Syntax check: still has an error on line {error.lineno}: {error.msg}."
    else:
        syntax_status = "Syntax check: the suggestion parses; runtime behavior was not checked."

    return (
        f"Suggested Code:\n{fixed}\n\n"
        f"Changes: {changes}\n{syntax_status}\n"
        "Review the suggestion before using it."
    )


def explain_error(code):
    """
    Checks for syntax errors in user-submitted code and returns
    a clean, user-friendly message without exposing internal tracebacks.
    """
    try:
        compile(code, "<user_input>", "exec")
        return "No syntax errors detected in your code.\nIt should be syntactically valid (runtime errors are still possible)."
    
    except SyntaxError as e:
        msg = "Syntax Error in the code you entered:\n\n"
        msg += f"→ {str(e)}\n"

        # Show the problematic line + arrow pointing to error
        if e.lineno is not None:
            lines = code.splitlines()
            if 1 <= e.lineno <= len(lines):
                bad_line = lines[e.lineno - 1].rstrip()
                msg += f"\nOn line {e.lineno}:\n"
                msg += f"  {bad_line}\n"
                
                if e.offset is not None and e.offset > 0:
                    msg += "  " + " " * (e.offset - 1) + "^ here\n"

        msg += "\nCommon causes and fixes:\n"
        msg += " • Missing colon   :     after def / if / for / while / class / with / else / elif\n"
        msg += "   Example:  def is_prime(n)    →    def is_prime(n):\n"
        msg += " • Indentation error (use 4 spaces consistently, don't mix tabs & spaces)\n"
        msg += " • Unclosed (, [, {, \" or '\n"
        msg += " • Typo in keyword (printt → print, etc.)\n"

        return msg

    except Exception as unexpected:
        # Very rare – something else went wrong during checking
        return f"Unexpected problem while checking syntax:\n{type(unexpected).__name__}: {str(unexpected)}"

class ExplanationVisitor(ast.NodeVisitor):
    def __init__(self, level):
        self.explanations = []
        self.level = level
        self.line_map = {}  # To map nodes to lines

    def visit(self, node):
        if hasattr(node, 'lineno'):
            line = node.lineno
            if self.level == "beginner":
                self.explain_beginner(node)
            elif self.level == "intermediate":
                self.explain_intermediate(node)
            elif self.level == "advanced":
                self.explain_advanced(node)
        self.generic_visit(node)

    def explain_beginner(self, node):
        if isinstance(node, ast.Assign):
            self.explanations.append(f"Line {node.lineno}: Assigning a value to a variable. Like storing something in a box.")
        elif isinstance(node, ast.If):
            self.explanations.append(f"Line {node.lineno}: Checking if something is true, and doing actions based on that.")
        elif isinstance(node, ast.For) or isinstance(node, ast.While):
            self.explanations.append(f"Line {node.lineno}: Repeating some code multiple times.")
        elif isinstance(node, ast.FunctionDef):
            self.explanations.append(f"Line {node.lineno}: Defining a reusable piece of code called a function.")
        elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            self.explanations.append(f"Line {node.lineno}: Bringing in external code or tools (modules).")

    def explain_intermediate(self, node):
        if isinstance(node, ast.Assign):
            target = ast.unparse(node.targets[0])
            value = ast.unparse(node.value)
            self.explanations.append(f"Line {node.lineno}: Assigning '{value}' to '{target}'.")
        elif isinstance(node, ast.If):
            test = ast.unparse(node.test)
            self.explanations.append(f"Line {node.lineno}: If condition '{test}' is True, execute the block.")
        elif isinstance(node, ast.For):
            target = ast.unparse(node.target)
            iter_ = ast.unparse(node.iter)
            self.explanations.append(f"Line {node.lineno}: Looping over '{iter_}', assigning each to '{target}'.")
        elif isinstance(node, ast.While):
            test = ast.unparse(node.test)
            self.explanations.append(f"Line {node.lineno}: While '{test}' is True, repeat the block.")
        elif isinstance(node, ast.FunctionDef):
            args = ', '.join(arg.arg for arg in node.args.args)
            self.explanations.append(f"Line {node.lineno}: Defining function '{node.name}' with parameters '{args}'.")
        elif isinstance(node, ast.Call):
            func = ast.unparse(node.func)
            self.explanations.append(f"Line {node.lineno}: Calling function '{func}'.")

    def explain_advanced(self, node):
        # More technical
        if isinstance(node, ast.Assign):
            self.explanations.append(f"Line {node.lineno}: Assignment statement. May involve unpacking if multiple targets.")
        elif isinstance(node, ast.If):
            self.explanations.append(f"Line {node.lineno}: Conditional branch. Supports elif/else chains.")
        elif isinstance(node, ast.For):
            self.explanations.append(f"Line {node.lineno}: Iterable loop. Handles else clause for no-break cases.")
        elif isinstance(node, ast.While):
            self.explanations.append(f"Line {node.lineno}: Condition-based loop. Also supports else clause.")
        elif isinstance(node, ast.FunctionDef):
            self.explanations.append(f"Line {node.lineno}: Function definition. May include decorators, type hints, etc.")
        elif isinstance(node, ast.Try):
            self.explanations.append(f"Line {node.lineno}: Exception handling block with try/except/else/finally.")

def explain_program(code, level="beginner"):
    levels = {"beginner", "intermediate", "advanced"}
    if level not in levels:
        level = "beginner"
    
    explanation = f"Detailed Program Explanation (Level: {level.title()}):\n\n"
    
    try:
        tree = ast.parse(code)
        visitor = ExplanationVisitor(level)
        visitor.visit(tree)
        
        if visitor.explanations:
            explanation += "Line-by-line/key structure explanations:\n" + "\n".join(visitor.explanations) + "\n\n"
        else:
            explanation += "No specific structures detected for detailed breakdown.\n\n"
        
        explanation += "Overall Flow:\n"
        explanation += "- The code starts executing from the top.\n"
        if level == "beginner":
            explanation += "- Imports (if any) load tools. Functions are defined but run when called. Main code runs directly.\n"
            explanation += "- Variables hold data, loops repeat actions, conditions make decisions.\n"
        elif level == "intermediate":
            explanation += "- Global code executes first, then any if __name__ == '__main__' block.\n"
            explanation += "- Watch for side effects like prints, inputs, or file operations.\n"
        elif level == "advanced":
            explanation += "- Execution model: Module-level code runs on import. Scopes: global, local, nonlocal.\n"
            explanation += "- Potential optimizations: Complexity analysis, e.g., loops may be O(n).\n"
        
        explanation += "\nTips:\n"
        if level == "beginner":
            explanation += "- Run it step-by-step in your mind or with print statements to debug.\n"
        elif level == "intermediate":
            explanation += "- Use a debugger like pdb to step through.\n"
        elif level == "advanced":
            explanation += "- Consider edge cases, exceptions, and performance.\n"
    
    except SyntaxError as e:
        explanation += f"Cannot fully explain due to syntax error: {str(e)}\n"
        explanation += "Fix syntax first for detailed breakdown.\n"
    
    return explanation
