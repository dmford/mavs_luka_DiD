# Mavericks Luka Difference-in-Differences Project

## Project Overview

This project analyzes the Dallas Mavericks’ performance before and after the Luka Doncic / Anthony Davis trade (treated as February 2, 2025) using a Difference-in-Differences (DiD) framework.

**Primary research question:**
How did the Dallas Mavericks’ performance change after trading away Luka Doncic, relative to the broader NBA control group, and how do injury timing and event-study dynamics affect interpretation?

This is an exploratory empirical project focused on learning, reproducibility, and progressively stronger causal design.

---

## Current Treatment Design

### Treated Team

* Dallas Mavericks (DAL)

### Treatment Date

* February 2, 2025
  (Luka Doncic traded away, Anthony Davis acquired)

### Control Group

* All NBA teams excluding:

  * Los Angeles Lakers (LAL)

The Lakers are excluded because Luka joined the Lakers immediately, which would contaminate the control group.

---

## Core Outcomes

### Binary Outcome

```text
win = 1 if win, 0 otherwise
```

### Continuous Outcome

```text
point_diff = PLUS_MINUS
```

Point differential preserves substantially more variation than binary wins/losses and is often more statistically informative.

---

## Symmetric Timeline Specifications

The project currently uses two main timing structures:

### 1. Game-Symmetric Window

Uses the number of post-trade Dallas games available and matches them with an equal number of pre-trade Dallas games.

**Example:**
If Dallas has 28 post-trade games:

* Pre: 28 games before trade
* Post: 28 games after trade

---

### 2. Calendar-Symmetric Window

Uses the number of post-trade calendar days available and matches the same number of pre-trade calendar days.

**Example:**
If 75 post-trade days are available:

* Pre: 75 days before trade
* Post: 75 days after trade

---

## Regression Specifications

### Baseline (No Controls)

```text
outcome ~ treated_team + post_trade + did
```

### Controlled Specification

```text
outcome ~ treated_team + post_trade + did
        + is_home
        + luka_injury_flag
        + ad_injury_flag
        + kyrie_injury_flag
        + C(opponent_abbr)
```

---

## Standard Errors

All models use:

### Clustered standard errors by `team_abbr`

This improves inference robustness relative to naive homoskedastic assumptions.

---

## Injury Controls

The project explicitly tracks injury-related game flags for:

### Luka Doncic

* Christmas Day 2024 calf injury currently flagged
* Additional missed games can be added

### Anthony Davis

* Mavericks injury dates framework included

### Kyrie Irving

* Injury framework included

### Aggregate

```text
any_mavs_star_injury_flag
```

This helps reduce bias from roster availability shocks around the trade window.

---

## Event Study Framework

The project now includes event-study bins for:

### Game-Based Timing

```text
event_bin_game
```

### Calendar-Based Timing

```text
event_bin_day
```

These bins allow:

* Pre-trend checks
* Timing scrutiny
* Immediate vs delayed treatment effect analysis

---

## Current Outputs

### Tables

Automatically generated in:

```text
./tables/
```

Examples:

* Descriptive statistics
* DiD results
* Controlled vs uncontrolled comparisons

### Graphs

Automatically generated in:

```text
./graphs/
```

Planned:

* Point differential scatterplots
* Pre/post visualizations
* Event-study figures

---

## Code Features

### Current Strengths

* Auto-clears terminal
* Auto-checks and installs dependencies
* Auto-creates output folders
* Auto-overwrites prior outputs
* Sequential table/graph naming
* Modular regression functions
* Multiple model specifications

---

## Major Current Limitations

This remains a deliberately simplified design.

### Important omitted or imperfectly measured confounders:

* Full injury history completeness
* Strength of schedule
* Kyrie role variation
* Other roster moves
* Coaching effects
* Back-to-backs / fatigue
* Team-specific trends
* Parallel trends assumptions not yet fully validated
* League-wide strategic shifts

---

## Planned Next Steps

### Near-Term

* Event-study regressions
* Point differential scatterplots
* Game/calendar split visual dashboards
* Expanded injury date lists
* Pre-trend coefficient plots

### Medium-Term

* Team fixed effects
* Date fixed effects
* Better injury precision
* Home/away interactions
* Placebo windows

### Long-Term

* Synthetic control methods
* Multi-season placebo analysis
* Better causal identification
* Comparative Lakers-perspective symmetry

---

## Educational Purpose

This project is intended to demonstrate:

* Difference-in-Differences design
* Regression workflow
* Visualization
* Model iteration
* Empirical coding discipline

It prioritizes:

### Transparency > premature causal certainty

---

## Repository Structure

```text
mavs_luka_DiD/
│
├── mavs_luka_DiD.py
├── README.md
├── tables/
└── graphs/
```

---

## Disclaimer

This project is exploratory and educational.

Current estimates should **not** be interpreted as definitive causal claims without stronger robustness checks, cleaner identification assumptions, and deeper injury/schedule validation.

---

## Author

**David Ford**
April 2026
