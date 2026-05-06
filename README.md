A toy compiler from [PL/0](https://en.wikipedia.org/wiki/PL/0) to Aarch64.
This is project for the course of Code Optimization and Transformation (a.y. 2025/2026) at Politecnico di Milano.

This project uses `uv`.

## How to run
```bash
uv run src/frontend.py input.txt
```

## How to test
You can install `qemu-aarch64` with `apt install -y qemu-user` on Ubuntu/Debian.

```bash
qemu--aarch64 ./a.out
```

## How to contribute
```bash
uv run ruff format
uv run ty check
uv run pytest
```
