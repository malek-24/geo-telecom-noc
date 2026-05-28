"""
datetime_tz.py — Dates affichées en fuseau Africa/Tunis (UTC+1, sans DST).
"""
from datetime import datetime
from zoneinfo import ZoneInfo

TZ_NAME = "Africa/Tunis"
TZ = ZoneInfo(TZ_NAME)

# Expression SQL : timestamp stocké (timestamptz ou timestamp) → chaîne locale Tunisie
SQL_TS_TN = (
    "to_char(({col} AT TIME ZONE 'UTC') AT TIME ZONE 'Africa/Tunis', "
    "'YYYY-MM-DD\"T\"HH24:MI:SS') || '+01:00'"
)


def sql_col_tunisia(column: str) -> str:
    """Retourne une expression SELECT pour formater une colonne date en heure Tunisie."""
    return SQL_TS_TN.format(col=column)


def format_dt_tunisia(dt) -> str | None:
    """Formate un datetime Python en ISO avec offset +01:00 (Tunisie)."""
    if dt is None:
        return None
    if getattr(dt, "tzinfo", None) is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    local = dt.astimezone(TZ)
    return local.strftime("%Y-%m-%dT%H:%M:%S+01:00")
