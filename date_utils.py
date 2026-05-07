# date_utils.py

from datetime import datetime, timedelta


DATE_FORMAT = "%Y-%m-%d"


def parse_date(date_text):
    """
    解析 YYYY-MM-DD 格式日期。
    """
    return datetime.strptime(date_text, DATE_FORMAT).date()


def format_date(date_obj):
    """
    格式化日期为 YYYY-MM-DD。
    """
    return date_obj.strftime(DATE_FORMAT)


def calculate_end_date(start_date, days):
    """
    根据开始日期和旅行天数计算结束日期。
    """
    start = parse_date(start_date)
    end = start + timedelta(days=days - 1)

    return format_date(end)


def build_travel_dates(start_date, days):
    """
    构造旅行日期信息。
    """
    return {
        "start_date": start_date,
        "end_date": calculate_end_date(start_date, days),
        "days": days
    }


def calculate_day_date(start_date, day_number):
    """
    根据出发日期和第几天计算当天日期。
    """
    start = parse_date(start_date)
    current = start + timedelta(days=day_number - 1)

    return format_date(current)


def days_from_today(target_date):
    """
    计算目标日期距离今天多少天。
    今天返回 0，明天返回 1，昨天返回 -1。
    """
    today = datetime.now().date()
    target = parse_date(target_date)

    return (target - today).days


def validate_date_format(date_text):
    """
    判断日期格式是否有效。
    """
    try:
        parse_date(date_text)
        return True
    except ValueError:
        return False
