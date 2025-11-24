from app.consumer import do_op

def test_do_op_reverse():
    assert do_op("reverse", "abc def") == "fed cba"
    assert do_op("REVERSE", "123") == "321"

def test_do_op_count_words():
    assert do_op("count_words", "one two three") == "3"
    assert do_op("count_words", "") == "0"

def test_do_op_count_letters():
    assert do_op("count_letters", "one two") == "6"  # 'one' (3) + 'two' (3)
    assert do_op("count_letters", "") == "0"

def test_do_op_upper_lower():
    assert do_op("uppercase", "aBc") == "ABC"
    assert do_op("lowercase", "aBc") == "abc"

def test_do_op_unknown():
    assert do_op("nonexistent", "data") == ""
