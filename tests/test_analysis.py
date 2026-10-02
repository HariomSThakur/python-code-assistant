from assistant.analysis import fix_missing_colon


def test_adds_missing_colon_to_if_header():
    code = "if score > 0\n    print(score)\n"
    expected = "if score > 0:\n    print(score)\n"

    assert fix_missing_colon(code) == expected


def test_leaves_valid_code_unchanged():
    code = "total = 2 + 3\n"

    assert fix_missing_colon(code) == code


def test_does_not_guess_at_unrelated_syntax_errors():
    code = "print('missing close'\n"

    assert fix_missing_colon(code) == code