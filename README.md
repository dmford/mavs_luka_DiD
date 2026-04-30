Continuous Outcome

point\_diff = PLUS\_MINUS



Point differential preserves substantially more variation than binary wins/losses and is often more statistically informative.



Symmetric Timeline Specifications



The project currently uses two main timing structures:



1\. Game-Symmetric Window



Uses the number of post-trade Dallas games available and matches them with an equal number of pre-trade Dallas games.



Example:



If Dallas has 28 post-trade games:



Pre: 28 games before trade

Post: 28 games after trade

2\. Calendar-Symmetric Window



Uses the number of post-trade calendar days available and matches the same number of pre-trade calendar days.



Example:



If 75 post-trade days are available:



Pre: 75 days before trade

Post: 75 days after trade

Regression Specifications

Baseline (No Controls)

outcome \~ treated\_team + post\_trade + did

Controlled Specification

outcome \~ treated\_team + post\_trade + did

&#x20;       + is\_home

&#x20;       + luka\_injury\_flag

&#x20;       + ad\_injury\_flag

&#x20;       + kyrie\_injury\_flag

&#x20;       + C(opponent\_abbr)

Standard Errors



All models use:



Clustered standard errors by team\_abbr



This improves inference robustness relative to naive homoskedastic assumptions.



Injury Controls



The project explicitly tracks injury-related game flags for:



Luka Doncic

Christmas Day 2024 calf injury currently flagged

Additional missed games can be added

Anthony Davis

Mavericks injury dates framework included

Kyrie Irving

Injury framework included

Aggregate:

any\_mavs\_star\_injury\_flag



This helps reduce bias from roster availability shocks around the trade window.



Event Study Framework



The project now includes event-study bins for:



Game-Based Timing

event\_bin\_game

Calendar-Based Timing

event\_bin\_day



These bins allow:



Pre-trend checks

Timing scrutiny

Immediate vs delayed treatment effect analysis

Current Outputs

Tables



Automatically generated in:



./tables/



Examples:



Descriptive statistics

DiD results

Controlled vs uncontrolled comparisons

Graphs



Automatically generated in:



./graphs/



Planned:



Point differential scatterplots

Pre/post visualizations

Event-study figures

Code Features

Current Strengths

Auto-clears terminal

Auto-checks and installs dependencies

Auto-creates output folders

Auto-overwrites prior outputs

Sequential table/graph naming

Modular regression functions

Multiple model specifications

Major Current Limitations



This remains a deliberately simplified design.



Important omitted or imperfectly measured confounders:

Full injury history completeness

Strength of schedule

Kyrie role variation

Other roster moves

Coaching effects

Back-to-backs / fatigue

Team-specific trends

Parallel trends assumptions not yet fully validated

League-wide strategic shifts

Planned Next Steps

Near-Term

Event-study regressions

Point differential scatterplots

Game/calendar split visual dashboards

Expanded injury date lists

Pre-trend coefficient plots

Medium-Term

Team fixed effects

Date fixed effects

Better injury precision

Home/away interactions

Placebo windows

Long-Term

Synthetic control methods

Multi-season placebo analysis

Better causal identification

Comparative Lakers-perspective symmetry

Educational Purpose



This project is intended to demonstrate:



Difference-in-Differences design

Regression workflow

Visualization

Model iteration

Empirical coding discipline



It prioritizes:



Transparency > premature causal certainty

Repository Structure

mavs\_luka\_DiD/

│

├── mavs\_luka\_DiD.py

├── README.md

├── tables/

└── graphs/

Disclaimer



This project is exploratory and educational.



Current estimates should not be interpreted as definitive causal claims without stronger robustness checks, cleaner identification assumptions, and deeper injury/schedule validation.



Author



David Ford

April 2026

