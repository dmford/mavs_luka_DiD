# mavs_luka_DiD

## Overview
A simple Python project using a Difference-in-Differences (DiD) approach to analyze Dallas Mavericks performance before and after the Luka Doncic trade.

This is an educational project focused on practicing data analysis, regression modeling, and visualization in Python.

## What it does
- Pulls NBA game data using `nba_api`
- Constructs treatment/control groups (Dallas vs rest of league)
- Runs basic DiD regressions
- Generates tables and figures automatically

## Outputs
- Tables → `./tables/`
- Figures → `./figures/`

## How to run
```bash
python mavs_luka_DiD.py
```

## Notes
- This is a simplified / learning-focused implementation
- Results are not intended as definitive causal claims

## Author
David Ford, assisted by ChatGPT
