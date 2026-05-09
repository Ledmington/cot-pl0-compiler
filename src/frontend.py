__doc__ = """PL/0 recursive descent parser adapted from Wikipedia"""

import argparse
import logging
import os
from pathlib import Path

import arm_ir
from cfg import CFG
from lexer import Lexer
from lowering import lowering
from parser import program
from support import (
    codeGeneration,
    flattening,
    layout,
    print_dotty,
)

logging.basicConfig(
    filename="error.log",
    filemode="w",
    format="[%(levelname)s][%(name)s] %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger("frontend")


def run(source: str, root_dir: Path = Path(os.getcwd())) -> None:
    """Run the compiler pipeline."""  # configurable target
    the_lexer = Lexer(source)
    res = program(the_lexer)

    res.navigate(lowering, post=True)
    res.navigate(flattening, post=True)
    logger.debug("\n {} \n".format(res))

    res.navigate(layout, post=True)

    print_dotty(res, root_dir / "log.dot")

    cfg = CFG(res)
    cfg.liveness()
    cfg.print_cfg_to_dot(root_dir / "cfg.dot")
    cfg.reg_alloc(n=arm_ir.target_info["available_registers"])

    res.navigate(codeGeneration)


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
