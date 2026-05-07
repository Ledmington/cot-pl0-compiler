from ir2 import CallExpression


def test_call_expr():
    actual = CallExpression(function="pippo", parameters=["pluto", 1])
    expected = ""
    assert expected == actual
