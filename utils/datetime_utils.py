from datetime import datetime, timezone


def get_current_utc_datetime() -> datetime:
    return datetime.now(timezone.utc)


def get_current_utc_datetime_str() -> str:
    return get_current_utc_datetime().strftime("%Y-%m-%d %H:%M:%S")


def get_current_utc_datetime_timestamp() -> int:
    return int(get_current_utc_datetime().timestamp())


def convert_any_datetime_to_utc(datetime_obj: datetime) -> datetime:
    return datetime_obj.astimezone(timezone.utc)


def convert_any_datetime_to_utc_str(datetime_obj: datetime) -> str:
    return convert_any_datetime_to_utc(datetime_obj).strftime("%Y-%m-%d %H:%M:%S")
