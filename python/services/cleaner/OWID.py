import warnings


import pandas as pd
from iso3166 import countries

from ..translator import translate_and_select_cols

warnings.simplefilter(action="ignore", category=FutureWarning)


def clean(covid):

    filename = "total.csv"
    df = pd.read_csv(f"{covid.path_to_save}/{filename}")

    all_countries = pd.DataFrame([c for c in countries])
    euro_countries = all_countries[
        all_countries.alpha2.isin(covid.countries_list)
    ]

    df = pd.merge(df, euro_countries, left_on="iso_code", right_on="alpha3")

    df_translated = translate_and_select_cols(df, covid)

    df_translated.date = pd.to_datetime(df_translated.date).dt.date

    df_melt = pd.melt(
        df_translated,
        id_vars=["date", "country"],
        value_vars=df_translated.columns.tolist().remove("date"),
        var_name="key",
        value_name="value",
    )

    df_melt["key"] = "owid_" + df_melt["key"]

    df_melt["source_url"] = covid.params["url"]
    df_melt["updated_on"] = pd.to_datetime(covid.dt_created)

    df_melt["filename"] = filename

    return df_melt
