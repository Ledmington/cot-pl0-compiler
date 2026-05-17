from printer import Printer


def test_nested_blocks():
    printer = Printer()
    printer += "Block {\n"
    printer.indent(1)
    printer += "a: 1\n"
    printer += "b: 2\n"
    printer += "c: {\n"
    printer.indent(1)
    printer += "content\n"
    printer.indent(-1)
    printer += "}\n"
    printer.indent(-1)
    printer += "}"
    assert (
        "\n".join(
            (
                "Block {",
                "  a: 1",
                "  b: 2",
                "  c: {",
                "    content",
                "  }",
                "}",
            )
        )
        == printer.__repr__()
    )


def test_variable_indent():
    printer = Printer()
    printer += "Block {\n"
    printer.indent(2)
    printer += "a: 1\n"
    printer += "b: 2\n"
    printer += "c: {\n"
    printer.indent(1)
    printer += "content\n"
    printer.indent(-1)
    printer += "}\n"
    printer.indent(-2)
    printer += "}"
    assert (
        "\n".join(
            (
                "Block {",
                "    a: 1",
                "    b: 2",
                "    c: {",
                "      content",
                "    }",
                "}",
            )
        )
        == printer.__repr__()
    )


def test_multiline():
    printer = Printer()
    printer += "Block {\n"
    printer.indent(1)
    printer += "a: 1\nb: 2\nc: 3\n"
    printer.indent(-1)
    printer += "}"
    assert (
        "\n".join(("Block {", "  a: 1", "  b: 2", "  c: 3", "}"))
        == printer.__repr__()
    )


def test_empty_line():
    printer = Printer()
    printer += "Block {\n"
    printer.indent(1)
    printer += ""
    printer.indent(-1)
    printer += "}"
    assert "\n".join(("Block {", "}")) == printer.__repr__()


def test_nested_empty_line():
    printer = Printer()
    printer.indent(1)
    printer += "Block {\n"
    printer.indent(1)
    printer += ""
    printer.indent(-1)
    printer += "}"
    printer.indent(-1)
    assert "\n".join(("  Block {", "  }")) == printer.__repr__()
