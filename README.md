# Dynamic Inventory Management System — Phase 2 PoC

This proof of concept implements the Phase 1 design with coordinated structures for product lookup, category lookup, FIFO restocking, and demand-aware decisions:

- a Python dictionary keyed by Product ID;
- a dictionary of sets for category membership; and
- a `deque` plus a membership set for duplicate-free FIFO restocking;
- a dictionary of bounded demand-history deques; and
- a dictionary of rolling totals for constant-time demand updates and averages.

`record_demand()` stores one fulfilled-demand observation per review period. The manager calculates a rolling average, raises the reorder point when forecast demand during lead time exceeds the product's static threshold, and returns a suggested replenishment quantity through `restock_recommendation()`.

The demand model is intentionally transparent for Phase 2. It uses a configurable rolling window, lead-time coverage, safety-stock periods, and review period; later phases can replace the moving average with seasonal or intermittent-demand forecasting without changing the public inventory interface.

## Run the demonstration

```bash
python demo.py
```

## Run the tests

```bash
python -m unittest -v
```

The project uses only the Python standard library and requires Python 3.10 or newer. Before submission, upload this folder to GitHub and replace the placeholder repository URL in the Phase 2 report.
