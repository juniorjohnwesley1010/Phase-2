# Dynamic Inventory Management System — Phase 2 PoC

This proof of concept implements the Phase 1 design with three coordinated structures:

- a Python dictionary keyed by Product ID;
- a dictionary of sets for category membership; and
- a `deque` plus a membership set for duplicate-free FIFO restocking.

## Run the demonstration

```bash
python demo.py
```

## Run the tests

```bash
python -m unittest -v
```

The project uses only the Python standard library and requires Python 3.10 or newer. Before submission, upload this folder to GitHub and replace the placeholder repository URL in the Phase 2 report.
