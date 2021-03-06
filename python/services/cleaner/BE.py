import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)

import pandas as pd
from datetime import date, timedelta

from ..translator import translate_and_select_cols


def _clean_excel(covid):

    filename = "COVID19BE.xlsx"
    source_file_path = f"{covid.path_to_save}/{filename}"

    ## CASES
    df_cases = pd.read_excel(
        source_file_path, sheet_name="CASES_AGESEX", engine="openpyxl"
    )
    df_cases_group = (
        df_cases[~df_cases["DATE"].isnull()].groupby(["DATE"]).sum()
    )
    df_cases_group["CASES"] = df_cases_group["CASES"].cumsum()
    df_translated = translate_and_select_cols(
        df_cases_group.reset_index(), covid
    )

    df_translated["date"] = pd.to_datetime(df_translated["date"]).dt.date
    df_melt_cases = pd.melt(
        df_translated,
        id_vars=["date"],
        value_vars=df_translated.columns.tolist().remove("date"),
        var_name="key",
        value_name="value",
    )

    # HOSP
    df_hosp = pd.read_excel(
        source_file_path, sheet_name="HOSP", engine="openpyxl"
    )
    df_hosp_group = df_hosp.groupby(["DATE"]).sum().reset_index()
    df_translated = translate_and_select_cols(df_hosp_group, covid)

    df_translated["date"] = pd.to_datetime(df_translated["date"]).dt.date
    df_melt_hosp = pd.melt(
        df_translated,
        id_vars=["date"],
        value_vars=df_translated.columns.tolist().remove("date"),
        var_name="key",
        value_name="value",
    )

    # TEST
    df_test = pd.read_excel(
        source_file_path, sheet_name="TESTS", engine="openpyxl"
    )

    df_translated = translate_and_select_cols(df_test, covid)

    df_translated["date"] = pd.to_datetime(df_translated["date"]).dt.date
    df_melt_test = pd.melt(
        df_translated,
        id_vars=["date"],
        value_vars=df_translated.columns.tolist().remove("date"),
        var_name="key",
        value_name="value",
    )

    df_melt = pd.concat([df_melt_cases, df_melt_hosp, df_melt_test], axis=0)

    df_melt["updated_on"] = pd.to_datetime(covid.dt_created)

    df_melt["source_url"] = covid.params["url"]
    df_melt["filename"] = filename
    df_melt["country"] = covid.country
    return df_melt


def _clean_apify(covid):

    filename = "total_apify.csv"
    source_file_path = f"{covid.data_path}/raw/{covid.dt_created}/{filename}"
    df = pd.read_csv(source_file_path)

    df_translated = translate_and_select_cols(df, covid)

    df_translated.date = pd.to_datetime(df_translated.date).dt.date

    df_melt = pd.melt(
        df_translated,
        id_vars=["date"],
        value_vars=df_translated.columns.tolist().remove("date"),
        var_name="key",
        value_name="value",
    )

    df_melt["updated_on"] = pd.to_datetime(covid.dt_created)
    df_melt["updated_on"] = df_melt["updated_on"].dt.date
    df_melt["source_url"] = covid.params["url_apify"]
    df_melt["filename"] = filename
    df_melt["country"] = covid.country

    df_melt = df_melt.drop_duplicates(["key", "date"], keep="last")

    return df_melt


def clean(covid):
    df_excel = _clean_excel(covid)
    df_apify = pd.DataFrame()  # _clean_apify(covid)

    df = pd.concat([df_excel, df_apify], axis=0)
    return df
