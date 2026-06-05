# Difference-in-Differences Analysis of the Luka Dončić / Anthony Davis Trade

This project uses observational NBA game data and quasi-experimental econometric methods to evaluate the impact of the February 2025 Luka Dončić / Anthony Davis trade on team performance.

Using a mirrored Difference-in-Differences framework, the analysis examines whether the Dallas Mavericks declined after trading Dončić and whether the Los Angeles Lakers improved after acquiring him.

The project was developed as an applied causal inference exercise in Python and focuses on research design, model specification, robustness checks, and interpretation rather than prediction.

## Research Question

How did the February 2025 Luka Dončić / Anthony Davis trade affect the performance of the Dallas Mavericks and Los Angeles Lakers?

The project uses a Difference-in-Differences framework to compare team performance before and after the trade while controlling for opponent quality, schedule effects, team fixed effects, and player availability.

## Methodology

The analysis uses publicly available NBA game logs obtained through `nba_api`.

Key empirical approaches include:

* Difference-in-Differences estimation
* Fixed effects modeling
* Observational data analysis
* Event-window robustness checks
* Injury-adjusted specifications

Two mirrored analyses are performed:

### Dallas Mavericks Analysis

* Treated team: Dallas Mavericks
* Excluded from controls: Los Angeles Lakers
* Injury controls: Luka Dončić pre-trade, Anthony Davis post-trade, Kyrie Irving throughout

### Los Angeles Lakers Analysis

* Treated team: Los Angeles Lakers
* Excluded from controls: Dallas Mavericks
* Injury controls: Anthony Davis pre-trade, Luka Dončić post-trade, LeBron James throughout

Primary outcomes include:

* Win probability
* Point differential

Preferred specifications include:

* Home/away controls
* Back-to-back indicators
* Opponent fixed effects
* Team fixed effects
* Star-player injury controls

## Main Findings

Results are directionally consistent with the trade harming Dallas and benefiting Los Angeles.

### Dallas Mavericks

The injury-adjusted specification estimates declines of approximately:

* 24.4 percentage points in win probability
* 13.4 points of point differential

### Los Angeles Lakers

The injury-adjusted specification estimates improvements of approximately:

* 15.1 percentage points in win probability
* 5.8 points of point differential

The mirrored nature of the results provides evidence consistent with a substantial performance shift following the trade.

## Important Caveat

This project should be interpreted as a descriptive empirical exercise rather than a definitive causal estimate.

Event-study pre-trend tests reject parallel pre-trends in both the Mavericks and Lakers analyses, indicating that the identifying assumptions required for a clean causal Difference-in-Differences interpretation are not fully satisfied.

The project therefore serves primarily as an applied causal inference and research-design exercise using observational data.

## Example Figures

### Dallas Mavericks

![Dallas point differential around trade](figures/mavs_luka_DiD_figure1.png)

### Los Angeles Lakers

![Lakers point differential around trade](figures/mavs_luka_DiD_figure5.png)

## Outputs

The script automatically generates:

* Regression tables
* Event-study visualizations
* Difference-in-Differences estimates
* Robustness checks

Representative outputs include:

* `tables/mavs_luka_DiD_table3.csv`
* `tables/mavs_luka_DiD_table11.csv`
* `figures/mavs_luka_DiD_figure1.png`
* `figures/mavs_luka_DiD_figure5.png`

## How to Run

Install dependencies:

```bash
pip install pandas statsmodels matplotlib nba_api
```

Run the analysis:

```bash
python mavs_luka_DiD.py
```

## Author

David Ford

This project was developed by David Ford with AI-assisted coding support (ChatGPT) used for debugging, documentation, workflow planning, and code review. Project design, implementation decisions, validation, interpretation, and final repository contents were reviewed and approved by the author.
