# ==================================================
# Project: mavs_luka_DiD.py
# Description: Naive Difference-in-Differences analysis of Dallas Mavericks wins
#              before/after the Luka Doncic / Anthony Davis trade.
# Author: David Ford
# Date: 2026-04-29
# ==================================================

# ==================================================
# 0a. DEPENDENCY CHECK + AUTO-INSTALL
# ==================================================
import importlib
import subprocess
import sys


REQUIRED_LIBRARIES = {
    "pandas": "pandas",
    "numpy": "numpy",
    "seaborn": "seaborn",
    "statsmodels": "statsmodels",
    "matplotlib": "matplotlib",
    "nba_api": "nba_api"
}


def ensure_libraries_installed():
    """
    Checks whether required libraries are installed.
    Installs missing libraries automatically via pip.
    """
    for import_name, pip_name in REQUIRED_LIBRARIES.items():
        try:
            importlib.import_module(import_name)

        except ImportError:
            print(f"Missing library detected: {pip_name}")
            print(f"Installing {pip_name}...\n")

            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pip_name]
            )

            print(f"{pip_name} installed successfully.\n")


# Run dependency check before standard imports
ensure_libraries_installed()


# ==================================================
# 0b. IMPORTS
# ==================================================

# Standard libraries
import os
from pathlib import Path

# Data and analysis
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
from nba_api.stats.endpoints import leaguegamefinder

# Tables and graphs
import matplotlib.pyplot as plt
from statsmodels.iolib.summary2 import summary_col


# ==================================================
# 0c. ENVIRONMENT SETUP
# ==================================================
def clear_terminal():
    """
    Clears terminal for clean script output.
    Works on Windows and Unix-based systems.
    """
    os.system("cls" if os.name == "nt" else "clear")


# ==================================================
# 0d. CONSTANTS
# ==================================================
TRADE_DATE = "2025-02-02"

TABLE_DIR = "./tables"
GRAPH_DIR = "./graphs"

table_counter = 1
graph_counter = 1

# Known / placeholder injury dates.
# These lists can be expanded as we verify additional missed games.

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
    os.makedirs(TABLE_DIR, exist_ok=True)
    os.makedirs(GRAPH_DIR, exist_ok=True)

    for file in os.listdir(TABLE_DIR):
        file_path = os.path.join(TABLE_DIR, file)
        if os.path.isfile(file_path):
            os.remove(file_path)

    for file in os.listdir(GRAPH_DIR):
        file_path = os.path.join(GRAPH_DIR, file)
        if os.path.isfile(file_path):
            os.remove(file_path)

    print("Old tables/graphs cleared. Starting fresh run...\n")


def get_next_table_path():
    """
    Returns next sequential table filename for current run.
    """
    global table_counter

    output_path = f"{TABLE_DIR}/mavs_luka_DiD_table{table_counter}.csv"
    table_counter += 1

    return output_path


def get_next_graph_path():
    """
    Returns next sequential graph filename for current run.
    """
    global graph_counter

    output_path = f"{GRAPH_DIR}/mavs_luka_DiD_graph{graph_counter}.png"
    graph_counter += 1

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

    # Point differential
    df["point_diff"] = df["PTS"] - df["PLUS_MINUS"] + df["PLUS_MINUS"]  # placeholder for readability
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
    # These are currently date-based flags and can be expanded as injury lists are updated.
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


def add_event_study_bins(df):
    """
    Creates binned event-study variables for both game-based and day-based timing.

    Game bins are based on relative_game_num.
    Calendar bins are based on relative_day_num.

    These bins are useful for checking pre-trends and whether effects appear
    immediately or gradually after the trade.
    """
    df = df.copy()

    game_bins = [-999, -21, -11, -6, -1, 0, 5, 10, 20, 999]
    game_labels = [
        "g_leq_minus_21",
        "g_minus_20_to_minus_11",
        "g_minus_10_to_minus_6",
        "g_minus_5_to_minus_1",
        "g_trade_day",
        "g_plus_1_to_plus_5",
        "g_plus_6_to_plus_10",
        "g_plus_11_to_plus_20",
        "g_geq_plus_21",
    ]

    day_bins = [-999, -61, -31, -15, -1, 0, 14, 30, 60, 999]
    day_labels = [
        "d_leq_minus_61",
        "d_minus_60_to_minus_31",
        "d_minus_30_to_minus_15",
        "d_minus_14_to_minus_1",
        "d_trade_day",
        "d_plus_1_to_plus_14",
        "d_plus_15_to_plus_30",
        "d_plus_31_to_plus_60",
        "d_geq_plus_61",
    ]

    df["event_bin_game"] = pd.cut(
        df["relative_game_num"],
        bins=game_bins,
        labels=game_labels,
        include_lowest=True
    )

    df["event_bin_day"] = pd.cut(
        df["relative_day_num"],
        bins=day_bins,
        labels=day_labels,
        include_lowest=True
    )

    return df


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
        "luka_injury_flag": "1 if Dallas game is flagged as Luka injury-related",
        "ad_injury_flag": "1 if Dallas game is flagged as AD injury-related",
        "kyrie_injury_flag": "1 if Dallas game is flagged as Kyrie injury-related",
        "any_mavs_star_injury_flag": "1 if Luka, AD, or Kyrie injury flag equals 1",
        "event_bin_game": "Binned game-relative event-study timing",
        "event_bin_day": "Binned calendar-relative event-study timing",
    }

    print("\n===== VARIABLE DESCRIPTIONS =====")
    for var, desc in variable_dict.items():
        print(f"{var}: {desc}")


# ==================================================
# 8. TABLE 1
# ==================================================
def create_table1(df):
    """
    Creates descriptive stats split by:
        window type
        treatment/control
        pre/post
    """
    summary = (
        df.groupby(["window_type", "treated_team", "post_trade"])
        .agg(
            games=("game_id", "count"),
            wins=("win", "sum"),
            losses=("loss", "sum")
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
        ["window_type", "group", "period", "games", "wins", "losses"]
    ]

    output_path = get_next_table_path()
    summary.to_csv(output_path, index=False)

    print(f"\nTable 1 saved to: {output_path}")

    return summary


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
def create_table2_did_results(df):
    """
    Runs multiple DiD specifications:
        Outcomes:
            win
            point_diff

        Specs:
            no controls
            with controls

        Windows:
            game_symmetric
            calendar_symmetric
    """
    results = []

    for window_type in sorted(df["window_type"].unique()):
        window_df = df[df["window_type"] == window_type].copy()

        for outcome_var in ["win", "point_diff"]:

            for use_controls in [False, True]:

                model = run_did_regression(
                    window_df,
                    outcome_var=outcome_var,
                    use_controls=use_controls
                )

                results.append({
                    "window_type": window_type,
                    "outcome": outcome_var,
                    "controls": "with_controls" if use_controls else "no_controls",
                    "did_estimate": model.params["did"],
                    "did_std_error": model.bse["did"],
                    "did_t_stat": model.tvalues["did"],
                    "did_p_value": model.pvalues["did"],
                    "n_observations": int(model.nobs),
                    "r_squared": model.rsquared
                })

    table2 = pd.DataFrame(results)

    table2 = table2[
        [
            "window_type",
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
    table2.to_csv(output_path, index=False)

    print(f"\nDiD results table saved to: {output_path}")

    return table2


# ==================================================
# 11. MAIN
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
    analysis_df = add_event_study_bins(analysis_df)

    print_dataset_overview(analysis_df)

    table1 = create_table1(analysis_df)
    did_results = create_table2_did_results(analysis_df)

    print("\n===== DESCRIPTIVE STATISTICS =====")
    print(table1)

    print("\n===== NAIVE DID RESULTS =====")
    print(did_results)

if __name__ == "__main__":
    main()