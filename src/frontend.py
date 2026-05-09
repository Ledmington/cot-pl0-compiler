__doc__ = """PL/0 recursive descent parser adapted from Wikipedia"""

import argparse
import logging
import os
from pathlib import Path

import arm_ir
from cfg import CFG
from codegen import codeGeneration
from flattening import flattening
from layout import layout
from lexer import Lexer
from lowering import lowering
from parser import parse_program
from support import print_dotty

logging.basicConfig(
    filename="error.log",
    filemode="w",
    format="[%(levelname)s][%(name)s] %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger("frontend")


def run(source: str, root_dir: Path = Path(os.getcwd())) -> None:
    """Run the compiler pipeline."""

    logger.debug("Parsing source")
    the_lexer = Lexer(source)
    program = parse_program(the_lexer)
    logger.debug("Parsing complete")

    logger.debug("Parsed program: {}".format(program))

    logger.debug("Start lowering")
    program.navigate(lowering, post=True)
    logger.debug("End lowering")

    logger.debug("Program after lowering: {}".format(program))

    logger.debug("Start flattening")
    program.navigate(flattening, post=True)
    logger.debug("End flattening")

    logger.debug("Program after flattening: {}".format(program))

    logger.debug("Start data layout")
    program.navigate(layout, post=True)
    logger.debug("End data layout")

    logger.debug("Program after data layout: {}".format(program))

    dotty_file = root_dir / "log.dot"
    logger.debug("Start printing dotty at '{}'", dotty_file)
    print_dotty(program, dotty_file)
    logger.debug("End printing dotty at '{}'", dotty_file)

    cfg = CFG(program)

    logger.debug("Start liveness analysis")
    cfg.liveness()
    logger.debug("End liveness analysis")

    logger.debug("Liveness analysis result: {}", cfg.print_liveness())

    cfg_dot_file = root_dir / "cfg.dot"
    logger.debug("Start printing CFG to dot at '{}'", cfg_dot_file)
    cfg.print_cfg_to_dot(cfg_dot_file)
    logger.debug("Start printing CFG to dot at '{}'", cfg_dot_file)

    logger.debug("Start register allocation")
    cfg.reg_alloc(n=arm_ir.target_info["available_registers"])
    logger.debug("End register allocation")

    logger.debug("Start code generation")
    program.navigate(codeGeneration)
    logger.debug("End code generation")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PL/0 recursive descent parser"
    )
    parser.add_argument("filename", help="Input source file")
    args = parser.parse_args()

    filename = args.filename
    logger.debug("Reading input source from {}".format(filename))
    source = open(filename, "r").read()

    logger.debug(
        """
*********************************************
    Starting debug with program '{}'
*********************************************
    """.format(filename)
    )

    logger.debug(
        """
***** Program '{}' source *****
{}
***** Program '{}' source *****
""".format(filename, source, filename)
    )

    root_dir = os.getcwd()

    run(source, root_dir=Path(root_dir))


if __name__ == "__main__":
    main()
