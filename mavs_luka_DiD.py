# ==================================================
# Project: mavs_luka_DiD.py
# Description: Naive Difference-in-Differences analysis of Dallas Mavericks wins
#              before/after the Luka Doncic / Anthony Davis trade.
# Author: David Ford
# Date: 2026-04-29
# ==================================================

# ==================================================
# 0a. IMPORTS
# ==================================================
import os
from pathlib import Path
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

from nba_api.stats.endpoints import leaguegamefinder


# ==================================================
# 0b. ENVIRONMENT SETUP
# ==================================================
def clear_terminal():
    """
    Clears terminal for clean script output.
    Works on Windows and Unix-based systems.
    """
    os.system("cls" if os.name == "nt" else "clear")


# ==================================================
# 0c. CONSTANTS
# ==================================================
TRADE_DATE = "2025-02-02"

SCRIPT_DIR = Path(__file__).resolve().parent

TABLE_DIR = SCRIPT_DIR / "tables"
FIGURE_DIR = SCRIPT_DIR / "figures"

table_counter = 1
figure_counter = 1

LUKA_LEFT_EARLY_DATES = ["2024-12-25"]
LUKA_MISSED_INJURY_DATES = []

AD_MAVS_LEFT_EARLY_DATES = []
AD_MAVS_MISSED_INJURY_DATES = []
KYRIE_MAVS_LEFT_EARLY_DATES = []
KYRIE_MAVS_MISSED_INJURY_DATES = []

AD_TRADED_AWAY_FROM_MAVS_DATE = "2026-02-06"


# ==================================================
# 0d. DESIGN NOTES
# ==================================================
"""
This is a deliberately naive Difference-in-Differences setup.

Main outcome:
    win = 1 if team won the game, 0 otherwise

Current focal comparison:
    Dallas Mavericks before/after trading away Luka Doncic and receiving
    Anthony Davis.

Control group:
    All NBA teams except the Lakers, since Luka was traded to the Lakers.

Major confounders intentionally ignored for now:
    - Other roster changes
    - Kyrie Irving availability
    - Strength of schedule
    - Home/away games
    - Back-to-backs and rest days
    - Other injuries
    - Coaching/strategy changes
    - Tanking/playoff incentives
    - The fact that the Luka and AD treatments are mechanically linked
"""


# ==================================================
# 1. OUTPUT DIRECTORY SETUP
# ==================================================
def ensure_directories():
    """
    Creates output directories and clears old outputs for a fresh script run.
    """
    TABLE_DIR.mkdir(exist_ok=True)
    FIGURE_DIR.mkdir(exist_ok=True)

    for file in TABLE_DIR.iterdir():
        if file.is_file():
            file.unlink()

    for file in FIGURE_DIR.iterdir():
        if file.is_file():
            file.unlink()

    print("Old tables/figures cleared. Starting fresh run...\n")


def get_next_table_path():
    """
    Returns next sequential table filename for current run.
    """
    global table_counter

    output_path = f"{TABLE_DIR}/mavs_luka_DiD_table{table_counter}.csv"
    table_counter += 1

    return output_path


def get_next_figure_path():
    """
    Returns next sequential figure filename for current run.
    """
    global figure_counter

    output_path = FIGURE_DIR / f"mavs_luka_DiD_figure{figure_counter}.png"
    figure_counter += 1

    return output_path


# ==================================================
# 2. DATA DOWNLOAD
# ==================================================
def get_regular_season_games(season="2024-25"):
    """
    Pull NBA regular-season team game logs only.

    SEASON_ID prefixes:
        1 = preseason
        2 = regular season
        3 = All-Star
        4 = playoffs

    For 2024-25 regular season, SEASON_ID should be 22024.
    """
    gamefinder = leaguegamefinder.LeagueGameFinder(
        season_nullable=season,
        league_id_nullable="00"
    )

    df = gamefinder.get_data_frames()[0]

    # Keep only regular-season NBA games
    df = df[df["SEASON_ID"].astype(str) == "22024"]

    return df


# ==================================================
# 3. DATA CLEANING
# ==================================================
def clean_game_data(df):
    """
    Standardizes columns for DiD use.
    """
    df = df.copy()

    # Extra safeguard: regular-season game IDs start with 002.
    df = df[df["GAME_ID"].astype(str).str.startswith("002")]

    df["game_date"] = pd.to_datetime(df["GAME_DATE"])
    df["team_abbr"] = df["TEAM_ABBREVIATION"]

    # Example MATCHUP values:
    #   DAL vs. BOS
    #   DAL @ BOS
    df["opponent_abbr"] = df["MATCHUP"].str[-3:]
    df["is_home"] = df["MATCHUP"].str.contains("vs.").astype(int)

    df["win"] = (df["WL"] == "W").astype(int)
    df["loss"] = (df["WL"] == "L").astype(int)

    # Point differential from the team's perspective
    df["point_diff"] = df["PLUS_MINUS"]

    df = df[
        [
            "GAME_ID",
            "game_date",
            "team_abbr",
            "opponent_abbr",
            "is_home",
            "win",
            "loss",
            "point_diff",
        ]
    ].rename(columns={"GAME_ID": "game_id"})

    return df


# ==================================================
# 4. DATE HELPERS
# ==================================================
def prepare_dates(df):
    """
    Adds relative_day_num and post_trade.
    """
    df = df.copy()

    trade_date = pd.to_datetime(TRADE_DATE)

    df["game_date"] = pd.to_datetime(df["game_date"])
    df["relative_day_num"] = (df["game_date"] - trade_date).dt.days
    df["post_trade"] = (df["game_date"] > trade_date).astype(int)

    return df


def add_relative_game_num(df, treated_team="DAL"):
    """
    Creates relative_game_num centered on the trade date from the perspective
    of the treated team's schedule.

    Last treated-team game before trade = -1
    First treated-team game after trade = +1

    Control-team games inherit the treated team's relative_game_num
    if they occur on the same calendar date.
    """
    df = df.copy()
    trade_date = pd.to_datetime(TRADE_DATE)

    treated_games = (
        df[df["team_abbr"] == treated_team]
        .sort_values("game_date")
        .copy()
    )

    pre_games = treated_games[treated_games["game_date"] < trade_date].copy()
    post_games = treated_games[treated_games["game_date"] > trade_date].copy()

    pre_games = pre_games.sort_values("game_date")
    post_games = post_games.sort_values("game_date")

    pre_games["relative_game_num"] = range(-len(pre_games), 0)
    post_games["relative_game_num"] = range(1, len(post_games) + 1)

    treated_schedule = pd.concat([pre_games, post_games])[
        ["game_date", "relative_game_num"]
    ]

    df = df.merge(
        treated_schedule,
        on="game_date",
        how="left"
    )

    return df


# ==================================================
# 5. TREATMENT FLAGGING
# ==================================================
def assign_treatment_control(df):
    """
    Dallas = treated.

    Lakers are excluded because Luka moved to the Lakers, which makes them
    contaminated for the Dallas-focused control group.
    """
    df = df.copy()

    df = df[~df["team_abbr"].isin(["LAL"])].copy()

    df["treated_team"] = (df["team_abbr"] == "DAL").astype(int)
    
    # Injury flags for Dallas games.
    # These are currently date-based and can be expanded as injury lists are updated.
    luka_injury_dates = pd.to_datetime(
        LUKA_LEFT_EARLY_DATES + LUKA_MISSED_INJURY_DATES
    )

    ad_injury_dates = pd.to_datetime(
        AD_MAVS_LEFT_EARLY_DATES + AD_MAVS_MISSED_INJURY_DATES
    )

    kyrie_injury_dates = pd.to_datetime(
        KYRIE_MAVS_LEFT_EARLY_DATES + KYRIE_MAVS_MISSED_INJURY_DATES
    )

    df["luka_injury_flag"] = (
        (df["team_abbr"] == "DAL")
        & (df["game_date"].isin(luka_injury_dates))
    ).astype(int)

    df["ad_injury_flag"] = (
        (df["team_abbr"] == "DAL")
        & (df["game_date"].isin(ad_injury_dates))
    ).astype(int)

    df["kyrie_injury_flag"] = (
        (df["team_abbr"] == "DAL")
        & (df["game_date"].isin(kyrie_injury_dates))
    ).astype(int)

    df["any_mavs_star_injury_flag"] = (
        (df["luka_injury_flag"] == 1)
        | (df["ad_injury_flag"] == 1)
        | (df["kyrie_injury_flag"] == 1)
    ).astype(int)

    df["did"] = df["treated_team"] * df["post_trade"]

    return df


# ==================================================
# 6. SYMMETRIC WINDOW HELPERS
# ==================================================
def make_game_symmetric_window(df):
    """
    Keeps games within a symmetric pre/post window based on the treated team's
    available post-trade games.
    """
    df = df.copy()

    max_post_games = df.loc[
        df["relative_game_num"] > 0,
        "relative_game_num"
    ].max()

    min_pre_game = -max_post_games

    window_df = df[
        (df["relative_game_num"] >= min_pre_game)
        & (df["relative_game_num"] <= max_post_games)
        & (df["relative_game_num"] != 0)
    ].copy()

    window_df["window_type"] = "game_symmetric"

    return window_df


def make_calendar_symmetric_window(df):
    """
    Keeps games within a symmetric pre/post window based on calendar days.
    """
    df = df.copy()

    max_post_days = df.loc[
        df["relative_day_num"] > 0,
        "relative_day_num"
    ].max()

    min_pre_day = -max_post_days

    window_df = df[
        (df["relative_day_num"] >= min_pre_day)
        & (df["relative_day_num"] <= max_post_days)
        & (df["relative_day_num"] != 0)
    ].copy()

    window_df["window_type"] = "calendar_symmetric"

    return window_df


def build_analysis_windows(df):
    """
    Creates both symmetric analysis datasets and stacks them together.
    """
    game_window = make_game_symmetric_window(df)
    calendar_window = make_calendar_symmetric_window(df)

    analysis_df = pd.concat(
        [game_window, calendar_window],
        ignore_index=True
    )

    return analysis_df


# ==================================================
# 7. DATASET INSPECTION
# ==================================================
def print_dataset_overview(df):
    """
    Prints top/bottom rows and variable descriptions.
    """
    print("\n===== TOP 5 ROWS =====")
    print(df.head())

    print("\n===== BOTTOM 5 ROWS =====")
    print(df.tail())

    variable_dict = {
        "game_id": "Unique NBA game identifier",
        "game_date": "Date of game",
        "team_abbr": "Team abbreviation",
        "opponent_abbr": "Opponent abbreviation",
        "is_home": "1 if home game, 0 if away",
        "win": "1 if win, 0 otherwise",
        "loss": "1 if loss, 0 otherwise",
        "relative_day_num": "Days relative to Luka trade",
        "relative_game_num": "Game number relative to treated team trade date",
        "post_trade": "1 if after Luka trade",
        "treated_team": "1 if Dallas Mavericks, 0 if control",
        "did": "treated_team * post_trade",
        "window_type": "game_symmetric or calendar_symmetric sample",
        "point_diff": "Team point differential",
        "luka_injury_flag": "1 if Dallas game is flagged as Luka injury-related",
        "ad_injury_flag": "1 if Dallas game is flagged as AD injury-related",
        "kyrie_injury_flag": "1 if Dallas game is flagged as Kyrie injury-related",
        "any_mavs_star_injury_flag": "1 if Luka, AD, or Kyrie injury flag equals 1",
    }

    print("\n===== VARIABLE DESCRIPTIONS =====")
    for var, desc in variable_dict.items():
        print(f"{var}: {desc}")


# ==================================================
# 8. TABLE 1
# ==================================================
def create_descriptive_tables_by_window(df):
    """
    Creates separate descriptive statistics tables for each window type.

    Each table is split by:
        treatment/control
        pre/post
    """
    tables = {}

    for window_type in sorted(df["window_type"].unique()):
        window_df = df[df["window_type"] == window_type].copy()

        summary = (
            window_df.groupby(["treated_team", "post_trade"])
            .agg(
                games=("game_id", "count"),
                wins=("win", "sum"),
                losses=("loss", "sum"),
                avg_point_diff=("point_diff", "mean")
            )
            .reset_index()
        )

        summary["group"] = summary["treated_team"].map(
            {1: "Treatment (DAL)", 0: "Control"}
        )

        summary["period"] = summary["post_trade"].map(
            {1: "Post", 0: "Pre"}
        )

        summary = summary[
            ["group", "period", "games", "wins", "losses", "avg_point_diff"]
        ]

        output_path = get_next_table_path()
        summary.to_csv(output_path, index=False)

        print(f"\nDescriptive statistics table saved for {window_type}: {output_path}")

        tables[window_type] = summary

    return tables


# ==================================================
# 9. REGRESSION HELPER
# ==================================================
def run_did_regression(
    df,
    outcome_var="win",
    use_controls=False
):
    """
    Runs DiD regression with optional controls.

    Base:
        outcome ~ treated_team + post_trade + did

    Controls:
        + is_home
        + luka_injury_flag
        + opponent fixed effects

    Standard errors:
        Clustered by team_abbr
    """
    df = df.copy()

    if use_controls:
        formula = (
            f"{outcome_var} ~ treated_team + post_trade + did "
            f"+ is_home + luka_injury_flag + ad_injury_flag + kyrie_injury_flag + C(opponent_abbr)"
        )
    else:
        formula = (
            f"{outcome_var} ~ treated_team + post_trade + did"
        )

    model = smf.ols(
        formula=formula,
        data=df
    ).fit(
        cov_type="cluster",
        cov_kwds={"groups": df["team_abbr"]}
    )

    return model


# ==================================================
# 10. REGRESSION TABLES
# ==================================================
def create_did_results_tables_by_window(df):
    """
    Runs DiD regressions separately by window type and saves one results table
    per window type.

    Each table includes:
        outcomes: win, point_diff
        specifications: no controls, with controls
    """
    tables = {}

    for window_type in sorted(df["window_type"].unique()):
        window_df = df[df["window_type"] == window_type].copy()

        results = []

        for outcome_var in ["win", "point_diff"]:
            for use_controls in [False, True]:

                model = run_did_regression(
                    window_df,
                    outcome_var=outcome_var,
                    use_controls=use_controls
                )

                results.append({
                    "outcome": outcome_var,
                    "controls": "with_controls" if use_controls else "no_controls",
                    "did_estimate": model.params["did"],
                    "did_std_error": model.bse["did"],
                    "did_t_stat": model.tvalues["did"],
                    "did_p_value": model.pvalues["did"],
                    "n_observations": int(model.nobs),
                    "r_squared": model.rsquared
                })

        results_table = pd.DataFrame(results)

        results_table = results_table[
            [
                "outcome",
                "controls",
                "did_estimate",
                "did_std_error",
                "did_t_stat",
                "did_p_value",
                "n_observations",
                "r_squared"
            ]
        ]

        output_path = get_next_table_path()
        results_table.to_csv(output_path, index=False)

        print(f"\nDiD results table saved for {window_type}: {output_path}")

        tables[window_type] = results_table

    return tables


# ==================================================
# 11. FIGURE HELPERS
# ==================================================
def create_point_diff_figures_by_window(df):
    """
    Creates point differential scatterplots separately for:
        calendar_symmetric
        game_symmetric

    Each graph shows:
        - Dallas observations
        - Control observations
        - Horizontal line at point_diff = 0
        - Vertical line at trade timing = 0
    """
    for window_type in sorted(df["window_type"].unique()):
        print(f"\nCreating figure for: {window_type}")

        window_df = df[df["window_type"] == window_type].copy()

        if window_type == "calendar_symmetric":
            x_var = "relative_day_num"
            x_label = "Days Relative to Trade"
            title = "Point Differential Around Trade: Calendar-Symmetric Window"

        elif window_type == "game_symmetric":
            x_var = "relative_game_num"
            x_label = "Games Relative to Trade"
            title = "Point Differential Around Trade: Game-Symmetric Window"

        else:
            continue

        treatment_df = window_df[window_df["treated_team"] == 1]
        control_df = window_df[window_df["treated_team"] == 0]

        fig, ax = plt.subplots(figsize=(10, 6))

        # Control teams (muted grey)
        ax.scatter(
            control_df[x_var],
            control_df["point_diff"],
            alpha=0.15,
            color="gray",
            label="Control teams"
        )

        # Dallas Mavericks (team blue)
        ax.scatter(
            treatment_df[x_var],
            treatment_df["point_diff"],
            alpha=0.9,
            color="#00538C",  # Mavericks blue
            label="Dallas Mavericks"
        )

        ax.axhline(
            y=0,
            linestyle="--",
            linewidth=1
        )

        ax.axvline(
            x=0,
            linestyle="--",
            linewidth=1
        )

        ax.set_title(title)
        ax.set_xlabel(x_label)
        ax.set_ylabel("Point Differential")
        ax.legend()

        plt.tight_layout()

        output_path = get_next_figure_path()
        fig.savefig(output_path, dpi=300, bbox_inches="tight")

        print(f"\nPoint differential figure saved for {window_type}: {output_path}")

        # Do not call plt.show() inside the loop, or the first graph blocks the second.

    # Show all created figures at once after both have been created.
    plt.show()


# ==================================================
# 12. MAIN
# ==================================================
def main():
    clear_terminal()
    print("Running mavs_luka_DiD.py ...\n")

    ensure_directories()

    raw_df = get_regular_season_games(season="2024-25")
    df = clean_game_data(raw_df)

    df = prepare_dates(df)
    df = assign_treatment_control(df)
    df = add_relative_game_num(df, treated_team="DAL")

    analysis_df = build_analysis_windows(df)

    print_dataset_overview(analysis_df)

    descriptive_tables = create_descriptive_tables_by_window(analysis_df)
    did_results_tables = create_did_results_tables_by_window(analysis_df)
    create_point_diff_figures_by_window(analysis_df)

    print("\n===== DESCRIPTIVE STATISTICS BY WINDOW =====")
    for window_type, table in descriptive_tables.items():
        print(f"\n--- {window_type} ---")
        print(table)

    print("\n===== NAIVE DID RESULTS BY WINDOW =====")
    for window_type, table in did_results_tables.items():
        print(f"\n--- {window_type} ---")
        print(table)

if __name__ == "__main__":
    main()


