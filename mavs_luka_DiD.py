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

LUKA_MISSED_INJURY_DATES = [
    "2024-11-17",
    "2024-11-22",
    "2024-11-24",
    "2024-11-25",
    "2024-11-27",
    "2024-11-30",
    "2024-12-19",
    "2024-12-21",
    "2024-12-27",
    "2024-12-28",
    "2024-12-30",
    "2025-01-01",
    "2025-01-03",
    "2025-01-06",
    "2025-01-07",
    "2025-01-09",
    "2025-01-12",
    "2025-01-14",
    "2025-01-15",
    "2025-01-17",
    "2025-01-20",
    "2025-01-22",
    "2025-01-23",
    "2025-01-25",
    "2025-01-27",
    "2025-01-29",
    "2025-01-31",
]

AD_MAVS_MISSED_INJURY_DATES = [
    "2025-02-04",
    "2025-02-06",
    "2025-02-10",
    "2025-02-12",
    "2025-02-13",
    "2025-02-21",
    "2025-02-23",
    "2025-02-25",
    "2025-02-27",
]

KYRIE_MAVS_MISSED_INJURY_DATES = [
    "2024-12-01",
    "2024-12-19",
    "2025-01-03",
    "2025-01-06",
    "2025-01-07",
    "2025-01-09",
    "2025-01-12",
    "2025-01-15",
    "2025-03-05",
    "2025-03-07",
    "2025-03-09",
    "2025-03-10",
    "2025-03-12",
    "2025-03-14",
    "2025-03-16",
    "2025-03-19",
    "2025-03-21",
    "2025-03-24",
    "2025-03-25",
    "2025-03-27",
    "2025-03-29",
    "2025-03-31",
    "2025-04-04",
    "2025-04-05",
    "2025-04-09",
    "2025-04-13",
]


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

    # --------------------------------------------------
    # BACK-TO-BACK (B2B) INDICATOR
    # --------------------------------------------------

    df = df.sort_values(["team_abbr", "game_date"])

    df["days_since_last_game"] = (
        df.groupby("team_abbr")["game_date"]
        .diff()
        .dt.days
    )

    df["is_back_to_back"] = (df["days_since_last_game"] == 1).astype(int)
    
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
    # Luka is used only pre-trade, AD only post-trade, and Kyrie across all periods.
    luka_injury_dates = pd.to_datetime(
        LUKA_MISSED_INJURY_DATES
    )

    ad_injury_dates = pd.to_datetime(
        AD_MAVS_MISSED_INJURY_DATES
    )

    kyrie_injury_dates = pd.to_datetime(
        KYRIE_MAVS_MISSED_INJURY_DATES
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

    df["pre_trade"] = 1 - df["post_trade"]

    df["luka_injury_pre"] = df["luka_injury_flag"] * df["pre_trade"]
    df["ad_injury_post"] = df["ad_injury_flag"] * df["post_trade"]

    df["did"] = df["treated_team"] * df["post_trade"]

    return df


# ==================================================
# 6. SYMMETRIC WINDOW HELPERS
# ==================================================
def make_main_game_symmetric_window(df):
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

    window_df["window_type"] = "main_game_symmetric"

    return window_df


def make_robust_calendar_symmetric_window(df):
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

    window_df["window_type"] = "robust_calendar_symmetric"

    return window_df


def build_analysis_windows(df):
    """
    Creates both symmetric analysis datasets and stacks them together.
    """
    game_window = make_main_game_symmetric_window(df)
    calendar_window = make_robust_calendar_symmetric_window(df)

    analysis_df = pd.concat(
        [game_window, calendar_window],
        ignore_index=True
    )

    return analysis_df

def add_event_study_bins(df):
    """
    Adds event-study bins for game-relative and calendar-relative timing.
    """
    df = df.copy()

    game_bins = [-33, -25, -17, -9, -1, 0, 8, 16, 24, 32]
    game_labels = [
        "g_minus_32_to_minus_25",
        "g_minus_24_to_minus_17",
        "g_minus_16_to_minus_9",
        "g_minus_8_to_minus_1",
        "g_trade_day",
        "g_plus_1_to_plus_8",
        "g_plus_9_to_plus_16",
        "g_plus_17_to_plus_24",
        "g_plus_25_to_plus_32",
    ]

    day_bins = [-999, -57, -43, -29, -15, -1, 0, 14, 28, 42, 56, 999]
    day_labels = [
        "d_leq_minus_57",
        "d_minus_56_to_minus_43",
        "d_minus_42_to_minus_29",
        "d_minus_28_to_minus_15",
        "d_minus_14_to_minus_1",
        "d_trade_day",
        "d_plus_1_to_plus_14",
        "d_plus_15_to_plus_28",
        "d_plus_29_to_plus_42",
        "d_plus_43_to_plus_56",
        "d_geq_plus_57",
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
        "days_since_last_game": "Days since this team's previous game",
        "is_back_to_back": "1 if team played on the previous calendar day",
        "win": "1 if win, 0 otherwise",
        "loss": "1 if loss, 0 otherwise",
        "relative_day_num": "Days relative to Luka trade",
        "relative_game_num": "Game number relative to treated team trade date",
        "post_trade": "1 if after Luka trade",
        "treated_team": "1 if Dallas Mavericks, 0 if control",
        "did": "treated_team * post_trade",
        "window_type": "main_game_symmetric or robust_calendar_symmetric sample",
        "point_diff": "Team point differential",
        "luka_injury_flag": "1 if Dallas game is flagged as Luka injury-related",
        "ad_injury_flag": "1 if Dallas game is flagged as AD injury-related",
        "kyrie_injury_flag": "1 if Dallas game is flagged as Kyrie injury-related",
        "any_mavs_star_injury_flag": "1 if Luka, AD, or Kyrie injury flag equals 1",
        "pre_trade": "1 if before Luka trade",
        "luka_injury_pre": "1 if Dallas pre-trade game is Luka injury-related",
        "ad_injury_post": "1 if Dallas post-trade game is AD injury-related",
        "event_bin_game": "Binned game-relative event-study timing",
        "event_bin_day": "Binned calendar-relative event-study timing",
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
    use_controls=False,
    use_injury_adjustment=False
):
    """
    Runs DiD regression with optional controls.

    Base:
        outcome ~ treated_team + post_trade + did

    FE/B2B controls:
        outcome ~ post_trade + did
            + is_home
            + is_back_to_back
            + opponent fixed effects
            + team fixed effects

    Injury adjustment:
        Adds Dallas-specific Luka/AD/Kyrie injury indicators as a sensitivity spec.

    Standard errors:
        Clustered by team_abbr
    """
    df = df.copy()

    if use_controls:
        formula = (
            f"{outcome_var} ~ post_trade + did "
            f"+ is_home "
            f"+ is_back_to_back "
            f"+ C(opponent_abbr) "
            f"+ C(team_abbr)"
        )
    else:
        formula = (
            f"{outcome_var} ~ treated_team + post_trade + did"
        )

    # Add Dallas-specific injury controls only for the injury-adjusted sensitivity spec.
    if use_injury_adjustment:
        formula += (
            f" + luka_injury_pre "
            f" + ad_injury_post "
            f" + kyrie_injury_flag"
        )

    model = smf.ols(
        formula=formula,
        data=df
    ).fit(
        cov_type="cluster",
        cov_kwds={"groups": df["team_abbr"]}
    )

    return model

def run_event_study_regression(df, window_type):
    """
    Runs event-study regression for a given window type.
    """
    df = df.copy()
    df = df[df["window_type"] == window_type].copy()

    if window_type == "main_game_symmetric":
        event_var = "event_bin_game"
        baseline = "g_minus_8_to_minus_1"
    else:
        event_var = "event_bin_day"
        baseline = "d_minus_14_to_minus_1"

    # Set omitted baseline category.
    # Patsy/statsmodels uses the FIRST category as the omitted reference group.
    df[event_var] = df[event_var].astype("category")

    ordered_categories = [baseline] + [
        cat for cat in df[event_var].cat.categories
        if cat != baseline
    ]

    df[event_var] = df[event_var].cat.reorder_categories(
        ordered_categories,
        ordered=True
    )

    formula = (
        f"point_diff ~ C({event_var}) * treated_team "
        f"+ is_home "
        f"+ is_back_to_back "
        f"+ luka_injury_pre "
        f"+ ad_injury_post "
        f"+ kyrie_injury_flag "
        f"+ C(opponent_abbr) "
        f"+ C(team_abbr)"
    )

    model = smf.ols(
        formula=formula,
        data=df
    ).fit(
        cov_type="cluster",
        cov_kwds={"groups": df["team_abbr"]}
    )

    return model, event_var

def extract_event_study_coefficients(model, event_var):
    """
    Extracts event-study interaction coefficients and cleans bin labels.
    """
    results = []

    for name, coef in model.params.items():

        if f"{event_var}" in name and "treated_team" in name:

            # Statsmodels names interaction terms like:
            # C(event_bin_game)[T.g_plus_1_to_plus_5]:treated_team
            bin_label = name.split("[T.")[1].split("]")[0]

            results.append({
                "bin": bin_label,
                "coef": coef,
                "se": model.bse[name]
            })

    return pd.DataFrame(results)


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
            for spec in ["no_controls", "with_fe_b2b_controls", "with_injury_adjustment"]:

                model = run_did_regression(
                    window_df,
                    outcome_var=outcome_var,
                    use_controls=(spec != "no_controls"),
                    use_injury_adjustment=(spec == "with_injury_adjustment")
                )

                results.append({
                    "outcome": outcome_var,
                    "controls": spec,
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

def create_event_study_summary_tables(df):
    """
    Creates event-study summary tables for game-relative and calendar-relative bins.
    """
    tables = {}

    specs = {
        "robust_calendar_symmetric": "event_bin_day",
        "main_game_symmetric": "event_bin_game",
    }

    for window_type, event_bin_var in specs.items():
        window_df = df[df["window_type"] == window_type].copy()

        summary = (
            window_df.groupby([event_bin_var, "treated_team"], observed=False)
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

        summary["event_bin_label"] = summary[event_bin_var].astype(str).map(
            get_event_bin_labels(window_type)
        )

        # Drop trade-day bin from event-study summary table.
        summary = summary[summary["event_bin_label"] != "Trade day"].copy()

        summary = summary[
            ["event_bin_label", "group", "games", "wins", "losses", "avg_point_diff"]
        ]

        output_path = get_next_table_path()
        summary.to_csv(output_path, index=False)

        print(f"\nEvent-study summary table saved for {window_type}: {output_path}")

        tables[window_type] = summary

    return tables


# ==================================================
# 11. FIGURE HELPERS
# ==================================================
def get_event_bin_midpoints(window_type):
    """
    Returns numeric midpoint values for event-study bins.
    Used only for cleaner event-study figure x-axes.
    """
    if window_type == "main_game_symmetric":
        return {
            "g_minus_32_to_minus_25": -28.5,
            "g_minus_24_to_minus_17": -20.5,
            "g_minus_16_to_minus_9": -12.5,
            "g_minus_8_to_minus_1": -4.5,
            "g_trade_day": 0,
            "g_plus_1_to_plus_8": 4.5,
            "g_plus_9_to_plus_16": 12.5,
            "g_plus_17_to_plus_24": 20.5,
            "g_plus_25_to_plus_32": 28.5,
        }

    return {
        "d_leq_minus_57": -63,
        "d_minus_56_to_minus_43": -49,
        "d_minus_42_to_minus_29": -35,
        "d_minus_28_to_minus_15": -21,
        "d_minus_14_to_minus_1": -7,
        "d_trade_day": 0,
        "d_plus_1_to_plus_14": 7,
        "d_plus_15_to_plus_28": 21,
        "d_plus_29_to_plus_42": 35,
        "d_plus_43_to_plus_56": 49,
        "d_geq_plus_57": 63,
    }

def get_event_bin_labels(window_type):
    """
    Returns human-readable labels for event-study bins.
    """
    if window_type == "main_game_symmetric":
        return {
            "g_minus_32_to_minus_25": "-32 to -25 games",
            "g_minus_24_to_minus_17": "-24 to -17 games",
            "g_minus_16_to_minus_9": "-16 to -9 games",
            "g_minus_8_to_minus_1": "-8 to -1 games",
            "g_trade_day": "Trade day",
            "g_plus_1_to_plus_8": "+1 to +8 games",
            "g_plus_9_to_plus_16": "+9 to +16 games",
            "g_plus_17_to_plus_24": "+17 to +24 games",
            "g_plus_25_to_plus_32": "+25 to +32 games",
        }

    return {
        "d_leq_minus_57": "≤ -57 days",
        "d_minus_56_to_minus_43": "-56 to -43 days",
        "d_minus_42_to_minus_29": "-42 to -29 days",
        "d_minus_28_to_minus_15": "-28 to -15 days",
        "d_minus_14_to_minus_1": "-14 to -1 days",
        "d_trade_day": "Trade day",
        "d_plus_1_to_plus_14": "+1 to +14 days",
        "d_plus_15_to_plus_28": "+15 to +28 days",
        "d_plus_29_to_plus_42": "+29 to +42 days",
        "d_plus_43_to_plus_56": "+43 to +56 days",
        "d_geq_plus_57": "≥ +57 days",
    }

def get_event_bin_short_labels(window_type):
    """
    Returns simplified labels for event-study plots.
    Labels use the endpoint farthest from the trade date.
    """
    if window_type == "main_game_symmetric":
        return {
            "g_minus_32_to_minus_25": "-32",
            "g_minus_24_to_minus_17": "-24",
            "g_minus_16_to_minus_9": "-16",
            "g_minus_8_to_minus_1": "-8",
            "g_trade_day": "0",
            "g_plus_1_to_plus_8": "+8",
            "g_plus_9_to_plus_16": "+16",
            "g_plus_17_to_plus_24": "+24",
            "g_plus_25_to_plus_32": "+32",
        }

    return {
        "d_leq_minus_57": "≤-57",
        "d_minus_56_to_minus_43": "-56",
        "d_minus_42_to_minus_29": "-42",
        "d_minus_28_to_minus_15": "-28",
        "d_minus_14_to_minus_1": "-14",
        "d_trade_day": "0",
        "d_plus_1_to_plus_14": "+14",
        "d_plus_15_to_plus_28": "+28",
        "d_plus_29_to_plus_42": "+42",
        "d_plus_43_to_plus_56": "+56",
        "d_geq_plus_57": "≥+57",
    }

def create_point_diff_figures_by_window(df):
    """
    Creates point differential scatterplots separately for:
        robust_calendar_symmetric
        main_game_symmetric

    Each graph shows:
        - Dallas observations
        - Control observations
        - Horizontal line at point_diff = 0
        - Vertical line at trade timing = 0
    """
    for window_type in sorted(df["window_type"].unique()):
        print(f"\nCreating figure for: {window_type}")

        window_df = df[df["window_type"] == window_type].copy()

        if window_type == "robust_calendar_symmetric":
            x_var = "relative_day_num"
            x_label = "Days Relative to Trade"
            title = "Point Differential Around Trade: Robustness 1 Calendar-Symmetric Window"

        elif window_type == "main_game_symmetric":
            x_var = "relative_game_num"
            x_label = "Games Relative to Trade"
            title = "Point Differential Around Trade: Main Game-Symmetric Window"

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

def create_event_study_plots(df):
    """
    Creates event-study coefficient plots for both window types.
    Uses numeric bin midpoints for clean x-axis labels.
    """
    for window_type in ["main_game_symmetric", "robust_calendar_symmetric"]:

        model, event_var = run_event_study_regression(df, window_type)
        coef_df = extract_event_study_coefficients(model, event_var)

        if window_type == "main_game_symmetric":
            baseline_bin = "g_minus_8_to_minus_1"
        else:
            baseline_bin = "d_minus_14_to_minus_1"

        baseline_row = pd.DataFrame([{
            "bin": baseline_bin,
            "coef": 0,
            "se": 0
        }])

        coef_df = pd.concat(
            [coef_df, baseline_row],
            ignore_index=True
        )

        coef_df["x"] = coef_df["bin"].map(
            get_event_bin_midpoints(window_type)
        )

        coef_df["event_bin_label"] = coef_df["bin"].map(
            get_event_bin_short_labels(window_type)
        )

        coef_df = coef_df.sort_values("x")

        # Drop trade-day bin from figure.
        coef_df = coef_df[coef_df["event_bin_label"] != "0"].copy()

        fig, ax = plt.subplots(figsize=(10, 6))

        ax.errorbar(
            x=coef_df["x"],
            y=coef_df["coef"],
            yerr=1.96 * coef_df["se"],
            fmt="o",
            capsize=4,
            linewidth=1.5
        )

        ax.set_xlim(coef_df["x"].min() - 5, coef_df["x"].max() + 5)

        ax.axhline(
            y=0,
            linestyle="--",
            linewidth=1,
            alpha=0.6
        )

        ax.axvline(
            x=0,
            linestyle="--",
            linewidth=1,
            alpha=0.6
        )

        if window_type == "main_game_symmetric":
            x_label = "Games Relative to Trade"
            title = "Event Study: Main Game-Symmetric Window"
        else:
            x_label = "Days Relative to Trade"
            title = "Event Study: Robustness 1 Calendar-Symmetric Window"

        ax.set_title(
            title + "\nRelative to final pre-trade bin"
        )

        ax.set_xlabel(f"{x_label} (Binned; labels show bin start)")
        ax.set_ylabel("Effect on Point Differential")

        ax.grid(
            axis="y",
            linestyle=":",
            linewidth=0.8,
            alpha=0.6
        )

        ax.set_xticks(coef_df["x"])
        ax.set_xticklabels(
            coef_df["event_bin_label"],
            rotation=0,
            ha="center"
        )

        y_min = coef_df["coef"].min() - 5
        y_max = coef_df["coef"].max() + 5
        ax.set_ylim(y_min, y_max)

        plt.tight_layout()

        output_path = get_next_figure_path()
        fig.savefig(output_path, dpi=300, bbox_inches="tight")

        print(f"\nEvent-study figure saved for {window_type}: {output_path}")

def create_event_study_coefficient_tables(df):
    """
    Saves event-study coefficient tables for both window types.
    Includes the omitted baseline bin as coef = 0.
    """
    tables = {}

    for window_type in ["main_game_symmetric", "robust_calendar_symmetric"]:

        model, event_var = run_event_study_regression(df, window_type)
        coef_df = extract_event_study_coefficients(model, event_var)

        if window_type == "main_game_symmetric":
            baseline_bin = "g_minus_8_to_minus_1"
        else:
            baseline_bin = "d_minus_14_to_minus_1"

        baseline_row = pd.DataFrame([{
            "bin": baseline_bin,
            "coef": 0,
            "se": 0,
        }])

        coef_df = pd.concat(
            [coef_df, baseline_row],
            ignore_index=True
        )

        coef_df["x"] = coef_df["bin"].map(
            get_event_bin_midpoints(window_type)
        )

        coef_df["event_bin_label"] = coef_df["bin"].map(
            get_event_bin_labels(window_type)
        )

        coef_df["ci_lower"] = coef_df["coef"] - 1.96 * coef_df["se"]
        coef_df["ci_upper"] = coef_df["coef"] + 1.96 * coef_df["se"]

        coef_df = coef_df.sort_values("x")

        # Drop trade-day bin from saved coefficient table.
        coef_df = coef_df[coef_df["event_bin_label"] != "Trade day"].copy()

        coef_df = coef_df[
            ["event_bin_label", "x", "coef", "se", "ci_lower", "ci_upper"]
        ]

        output_path = get_next_table_path()
        coef_df.to_csv(output_path, index=False)

        print(f"\nEvent-study coefficient table saved for {window_type}: {output_path}")

        tables[window_type] = coef_df

    return tables

def run_pretrend_test(df):
    """
    Tests whether all pre-treatment event-study coefficients are jointly zero.
    """
    print("\n" + "=" * 60)
    print("PRE-TREND TEST")
    print("=" * 60)

    for window_type in ["main_game_symmetric", "robust_calendar_symmetric"]:

        model, event_var = run_event_study_regression(df, window_type)

        if window_type == "main_game_symmetric":
            pre_bins = [
                "g_minus_32_to_minus_25",
                "g_minus_24_to_minus_17",
                "g_minus_16_to_minus_9"
            ]
        else:
            pre_bins = [
                "d_leq_minus_57",
                "d_minus_56_to_minus_43",
                "d_minus_42_to_minus_29",
                "d_minus_28_to_minus_15"
            ]

        terms = [
            f"C({event_var})[T.{b}]:treated_team"
            for b in pre_bins
        ]

        hypothesis = " = 0, ".join(terms) + " = 0"

        test = model.f_test(hypothesis)

        print(f"\n--- {window_type} ---")
        f_stat = float(test.fvalue)
        p_value = float(test.pvalue)

        print(f"F-stat: {f_stat:.3f}")
        print(f"p-value: {p_value:.4f}")


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
    analysis_df = add_event_study_bins(analysis_df)

    analysis_df_no_luka = analysis_df[
        analysis_df["luka_injury_pre"] == 0
    ].copy()

    print_dataset_overview(analysis_df)

    descriptive_tables = create_descriptive_tables_by_window(analysis_df)
    did_results_tables = create_did_results_tables_by_window(analysis_df)

    print("\n===== DID RESULTS (EXCLUDING LUKA INJURY GAMES) =====")
    did_results_no_luka = create_did_results_tables_by_window(analysis_df_no_luka)

    for window_type, table in did_results_no_luka.items():
        print(f"\n--- {window_type} (no Luka injury games) ---")
        print(table)

    event_study_summary_tables = create_event_study_summary_tables(analysis_df)
    event_study_coefficient_tables = create_event_study_coefficient_tables(analysis_df)

    run_pretrend_test(analysis_df)

    print("\n===== BIN SAMPLE SIZES =====")
    for window_type, table in event_study_summary_tables.items():
        print(f"\n--- {window_type} ---")
        print(table[["event_bin_label", "group", "games"]])
    
    create_point_diff_figures_by_window(analysis_df)
    create_event_study_plots(analysis_df)

    print("\n===== DESCRIPTIVE STATISTICS BY WINDOW =====")
    for window_type, table in descriptive_tables.items():
        print(f"\n--- {window_type} ---")
        print(table)

    print("\n===== NAIVE DID RESULTS BY WINDOW =====")
    for window_type, table in did_results_tables.items():
        print(f"\n--- {window_type} ---")
        print(table)

    print("\n===== EVENT-STUDY SUMMARY TABLES =====")
    for window_type, table in event_study_summary_tables.items():
        print(f"\n--- {window_type} ---")
        print(table)

    print("\n===== EVENT-STUDY COEFFICIENT TABLES =====")
    for window_type, table in event_study_coefficient_tables.items():
        print(f"\n--- {window_type} ---")
        print(table)

    plt.show()

if __name__ == "__main__":
    main()