from ir2 import CallExpression


def test_call_expr():
    actual = CallExpression(
        function="pippo", parameters=["pluto", 1]
    ).__repr__()
    expected = "CallExpression(['pippo', 'pluto', 1])"
    assert expected == actual
