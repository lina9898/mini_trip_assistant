# exporter.py

import os
from datetime import datetime
from html import escape
from pathlib import Path


EXPORT_DIR = "exports"


def ensure_export_dir():
    """
    确保导出文件夹存在。
    """
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)


def safe_filename(text):
    """
    处理文件名中的特殊字符。
    """
    text = str(text)
    for char in ['/', '\\', ' ', ':', '*', '?', '"', '<', '>', '|']:
        text = text.replace(char, "_")

    return text


def build_export_filename(trip_data, suffix="md"):
    """
    根据目的地和当前时间生成导出文件名。
    """
    destination = trip_data.get("destination", "未知目的地")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"{safe_filename(destination)}_旅行报告_{timestamp}.{suffix}"


def export_trip_to_markdown(
    trip_data,
    budget=None,
    location_info=None,
    weather_info=None,
    hotel_info=None,
    transport_info=None,
    opening_hours_info=None,
    event_info=None
):
    """
    将旅行计划导出为 Markdown 文件。
    """
    ensure_export_dir()

    filename = build_export_filename(trip_data, suffix="md")
    filepath = os.path.join(EXPORT_DIR, filename)

    markdown_text = build_markdown_report(
        trip_data=trip_data,
        budget=budget,
        location_info=location_info,
        weather_info=weather_info,
        hotel_info=hotel_info,
        transport_info=transport_info,
        opening_hours_info=opening_hours_info,
        event_info=event_info
    )

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(markdown_text)

    return filepath


def build_markdown_report(
    trip_data,
    budget=None,
    location_info=None,
    weather_info=None,
    hotel_info=None,
    transport_info=None,
    opening_hours_info=None,
    event_info=None
):
    """
    根据 trip_data、budget、location_info、weather_info 生成 Markdown 文本。
    """
    budget = budget or {}
    location_info = location_info or {}
    weather_info = weather_info or {}
    hotel_info = hotel_info or {}
    transport_info = transport_info or {}
    opening_hours_info = opening_hours_info or {}
    event_info = event_info or {}

    origin = trip_data.get("origin") or transport_info.get("origin")
    destination = trip_data.get("destination", "未知目的地")
    days = trip_data.get("days", "未知")
    preference = trip_data.get("preference", "未填写")
    pace = trip_data.get("pace", "适中")
    budget_level = trip_data.get("budget_level", "中")
    people = trip_data.get("people", budget.get("people", 1))
    travel_dates = trip_data.get("travel_dates", {})
    start_date = trip_data.get("start_date") or travel_dates.get("start_date")
    end_date = trip_data.get("end_date") or travel_dates.get("end_date")

    weather_summary = trip_data.get("weather_summary", "暂无天气摘要。")
    weather_adjustment = trip_data.get("weather_adjustment", "暂无天气适配说明。")
    route_strategy = trip_data.get("route_strategy", "暂无路线策略说明。")
    transport_advice = trip_data.get("transport_advice", "暂无交通建议。")
    intercity_transport_advice = trip_data.get("intercity_transport_advice", "暂无城际交通建议。")
    hotel_advice = trip_data.get("hotel_advice", "暂无住宿选址建议。")
    event_advice = trip_data.get("event_advice", "暂无城市活动建议。")
    backup_plan = trip_data.get("backup_plan", "暂无备选方案。")
    suitable_for = trip_data.get("suitable_for", "暂无适合人群说明。")
    advice = trip_data.get("advice", "暂无旅行建议。")
    edit_summary = trip_data.get("edit_summary")
    plan = trip_data.get("plan", [])

    lines = []
    lines.append(f"# {destination}旅行计划")
    lines.append("")
    lines.append(f"> 导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    lines.append("## 一、基础信息")
    lines.append("")
    if origin:
        lines.append(f"- 出发地：{origin}")
    lines.append(f"- 目的地：{destination}")
    if start_date and end_date:
        lines.append(f"- 出行日期：{start_date} 至 {end_date}")
    elif start_date:
        lines.append(f"- 出行日期：{start_date}")
    lines.append(f"- 旅行天数：{days} 天")
    lines.append(f"- 出行人数：{people} 人")
    lines.append(f"- 旅行偏好：{preference}")
    lines.append(f"- 旅行节奏：{pace}")
    lines.append(f"- 预算档位：{budget_level}")
    lines.append("")

    if edit_summary:
        lines.append("## 二、本次修改说明")
        lines.append("")
        lines.append(edit_summary)
        lines.append("")

    lines.append("## 三、目的地信息")
    lines.append("")
    if location_info.get("success"):
        lines.append(f"- 标准地址：{location_info.get('formatted_address')}")
        lines.append(f"- 省份：{location_info.get('province')}")
        lines.append(f"- 城市：{location_info.get('city')}")
        lines.append(f"- 行政区编码：{location_info.get('adcode')}")
        lines.append(f"- 经度：{location_info.get('longitude')}")
        lines.append(f"- 纬度：{location_info.get('latitude')}")
    else:
        lines.append(f"- 地图信息：{location_info.get('error', '暂无地图信息')}")
    lines.append("")

    lines.append("## 四、天气信息")
    lines.append("")
    if weather_info.get("success"):
        lines.append(f"- 城市：{weather_info.get('city')}")
        lines.append(f"- 天气模式：{weather_info.get('mode', 'live')}")
        if weather_info.get("mode") == "forecast":
            for item in weather_info.get("forecasts", []):
                lines.append(
                    f"- {item.get('date')}：白天 {item.get('dayweather')} "
                    f"{item.get('daytemp')}℃，夜间 {item.get('nightweather')} "
                    f"{item.get('nighttemp')}℃"
                )
        else:
            lines.append(f"- 天气：{weather_info.get('weather')}")
            lines.append(f"- 温度：{weather_info.get('temperature')}℃")
            lines.append(f"- 风向：{weather_info.get('winddirection')}")
            lines.append(f"- 风力：{weather_info.get('windpower')}")
            lines.append(f"- 湿度：{weather_info.get('humidity')}%")
        lines.append(f"- 发布时间：{weather_info.get('reporttime')}")
        if weather_info.get("note"):
            lines.append(f"- 说明：{weather_info.get('note')}")
    else:
        lines.append(f"- 天气信息：{weather_info.get('error', '暂无天气信息')}")
        if weather_info.get("note"):
            lines.append(f"- 说明：{weather_info.get('note')}")
    lines.append("")

    lines.append("## 五、智能适配分析")
    lines.append("")
    lines.append(f"**天气摘要：** {weather_summary}")
    lines.append("")
    lines.append(f"**天气适配：** {weather_adjustment}")
    lines.append("")
    lines.append(f"**路线策略：** {route_strategy}")
    lines.append("")
    lines.append(f"**交通建议：** {transport_advice}")
    lines.append("")
    lines.append(f"**出发地到目的地交通建议：** {intercity_transport_advice}")
    lines.append("")
    lines.append(f"**住宿选址建议：** {hotel_advice}")
    lines.append("")
    lines.append(f"**雨天备选方案：** {backup_plan}")
    lines.append("")

    lines.append("## 六、每日行程安排")
    lines.append("")
    for day_plan in plan:
        day = day_plan.get("day", "")
        date = day_plan.get("date")
        if date:
            lines.append(f"### 第 {day} 天（{date}）")
        else:
            lines.append(f"### 第 {day} 天")
        lines.append("")
        lines.append(f"- 上午：{day_plan.get('morning', '')}")
        lines.append(f"- 下午：{day_plan.get('afternoon', '')}")
        lines.append(f"- 晚上：{day_plan.get('evening', '')}")
        lines.append(f"- 说明：{day_plan.get('note', '')}")
        lines.append(f"- 推荐理由：{day_plan.get('reason', '')}")
        lines.append("")

    lines.append("## 七、开放时间检查")
    lines.append("")
    opening_checks = opening_hours_info.get("checks", [])
    risk_items = [
        item for item in opening_checks
        if item.get("risk_level") in ["high", "medium"]
    ]
    if risk_items:
        for item in risk_items[:8]:
            lines.append(
                f"- 第 {item.get('day')} 天 {item.get('period')}｜"
                f"{item.get('place_name')}｜{item.get('risk_level')}｜{item.get('message')}"
            )
        summary = opening_hours_info.get("summary", {})
        lines.append(f"- 建议：{summary.get('suggestion', '建议出行前确认官方开放时间。')}")
    else:
        lines.append("暂未发现明显开放时间风险，但出行前仍建议确认官方信息。")
    lines.append("")

    lines.append("## 八、城市活动与特殊事件")
    lines.append("")
    event_summary = event_info.get("summary", {})
    event_items = event_info.get("events", [])
    lines.append(event_advice or event_summary.get("suggestion", "暂未查询到明确活动信息。"))
    lines.append("")
    if event_items:
        for event in event_items[:8]:
            lines.append(
                f"- {event.get('date', '')} {event.get('time', '')}｜"
                f"{event.get('name', '')}｜{event.get('venue', '')}｜"
                f"{event.get('category', '')}｜{event.get('recommendation', '')}"
            )
    else:
        lines.append(f"- {event_summary.get('suggestion', '暂未查询到明确活动信息。')}")
    if event_info.get("note"):
        lines.append(f"- 说明：{event_info.get('note')}")
    lines.append("")

    lines.append("## 九、预算估算")
    lines.append("")
    if budget:
        lines.append(f"- 住宿费用：{budget.get('hotel', 0)} 元")
        lines.append(f"- 餐饮费用：{budget.get('food', 0)} 元")
        lines.append(f"- 交通费用：{budget.get('transport', 0)} 元")
        lines.append(f"- 门票费用：{budget.get('ticket', 0)} 元")
        lines.append(f"- 人均预算：{budget.get('single_person_total', 0)} 元")
        lines.append(f"- 预计总预算：{budget.get('total', 0)} 元")
    else:
        lines.append("暂无预算信息。")
    lines.append("")

    lines.append("## 十、出发地到目的地交通建议")
    lines.append("")
    recommendation = transport_info.get("recommendation", {})
    driving = transport_info.get("driving", {})
    transit = transport_info.get("transit", {})
    lines.append(intercity_transport_advice)
    lines.append("")
    lines.append(f"- 推荐方式：{recommendation.get('main_mode', '暂无')}")
    lines.append(f"- 推荐理由：{recommendation.get('reason', '暂无')}")
    lines.append(f"- 第一天安排建议：{recommendation.get('first_day_advice', '暂无')}")
    lines.append(f"- 驾车距离：{driving.get('distance_km', '未知')} km")
    lines.append(f"- 驾车耗时：{driving.get('duration_hour', '未知')} 小时")
    lines.append(f"- 公共交通耗时：{transit.get('duration_hour', '未知')} 小时")
    if transport_info.get("note"):
        lines.append(f"- 说明：{transport_info.get('note')}")
    lines.append("")

    lines.append("## 十一、住宿选址建议")
    lines.append("")
    lines.append(hotel_advice)
    lines.append("")
    if hotel_info:
        lines.append(f"- 区域建议：{hotel_info.get('area_suggestion', '暂无区域建议')}")
        for hotel in hotel_info.get("hotel_candidates", [])[:5]:
            lines.append(
                f"- {hotel.get('name')}｜{hotel.get('district')}｜"
                f"平均距离：{hotel.get('avg_distance_km')} km｜"
                f"最近景点：{hotel.get('nearest_place')}｜{hotel.get('reason')}"
            )
    lines.append("")

    lines.append("## 十二、适合人群")
    lines.append("")
    lines.append(suitable_for)
    lines.append("")

    lines.append("## 十三、旅行建议")
    lines.append("")
    lines.append(advice)
    lines.append("")

    return "\n".join(lines)


def export_trip_to_html(
    trip_data,
    budget=None,
    location_info=None,
    weather_info=None,
    image_info=None,
    hotel_info=None,
    transport_info=None,
    opening_hours_info=None,
    event_info=None
):
    """
    将旅行计划导出为 HTML 文件。
    """
    ensure_export_dir()

    filename = build_export_filename(trip_data, suffix="html")
    filepath = os.path.join(EXPORT_DIR, filename)

    html_text = build_html_report(
        trip_data=trip_data,
        budget=budget,
        location_info=location_info,
        weather_info=weather_info,
        image_info=image_info,
        hotel_info=hotel_info,
        transport_info=transport_info,
        opening_hours_info=opening_hours_info,
        event_info=event_info
    )

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(html_text)

    return filepath


def build_info_list(items):
    html_items = "".join(
        f"<li><strong>{escape(str(label))}：</strong>{escape(str(value))}</li>"
        for label, value in items
    )
    return f"<ul>{html_items}</ul>"


def build_image_gallery(image_info):
    image_info = image_info or {}
    if image_info.get("day_images"):
        return ""

    photos = image_info.get("photos", [])[:6]

    if not photos:
        return ""

    photo_cards = ""

    for photo in photos:
        image_url = photo.get("image_url")
        if not image_url:
            continue

        description = photo.get("description") or "旅行图片"
        query = photo.get("query") or ""
        photographer_name = photo.get("photographer_name") or "Unsplash Photographer"
        photographer_profile = photo.get("photographer_profile") or "#"
        photo_page = photo.get("photo_page") or "#"
        query_line = f"<p class=\"photo-query\">匹配：{escape(query)}</p>" if query else ""

        photo_cards += f"""
        <div class="photo-card">
            <img src="{escape(image_url)}" alt="{escape(description)}">
            <div class="photo-caption">
                <p>{escape(description)}</p>
                {query_line}
                <p class="photo-credit">
                    Photo by <a href="{escape(photographer_profile)}" target="_blank">{escape(photographer_name)}</a>
                    on <a href="{escape(photo_page)}" target="_blank">Unsplash</a>
                </p>
            </div>
        </div>
        """

    if not photo_cards:
        return ""

    return f"""
    <section class="section">
        <h2>旅行灵感图片</h2>
        <div class="photo-grid">
            {photo_cards}
        </div>
    </section>
    """


def build_place_image_cards(place_images):
    """
    生成某一天的地点图片卡片 HTML。
    """
    if not place_images:
        return ""

    cards = ""

    for image in place_images:
        image_url = image.get("image_url")
        place_name = image.get("place_name", "行程地点")
        description = image.get("description") or place_name
        source = image.get("source")
        credit = image.get("credit", "")

        if not image_url:
            continue

        if source == "unsplash":
            photographer_name = image.get("photographer_name") or "Unsplash Photographer"
            photographer_profile = image.get("photographer_profile") or "#"
            photo_page = image.get("photo_page") or "#"
            credit_html = f"""
            Photo by <a href="{escape(str(photographer_profile))}" target="_blank">{escape(str(photographer_name))}</a>
            on <a href="{escape(str(photo_page))}" target="_blank">Unsplash</a>
            """
        else:
            credit_html = escape(str(credit or "图片来源：高德 POI"))

        cards += f"""
        <div class="photo-card">
            <img src="{escape(str(image_url))}" alt="{escape(str(description))}">
            <div class="photo-caption">
                <p><strong>{escape(str(place_name))}</strong></p>
                <p>{escape(str(description))}</p>
                <p class="photo-credit">{credit_html}</p>
            </div>
        </div>
        """

    if not cards:
        return ""

    return f"""
    <div class="photo-grid day-photo-grid">
        {cards}
    </div>
    """


def build_opening_hours_section(opening_hours_info):
    """
    生成开放时间风险 HTML。
    """
    if not opening_hours_info:
        return ""

    checks = opening_hours_info.get("checks", [])
    summary = opening_hours_info.get("summary", {})
    risk_items = [
        item for item in checks
        if item.get("risk_level") in ["high", "medium"]
    ]

    if not risk_items:
        return f"""
        <section class="section">
            <h2>开放时间检查</h2>
            <p>暂未发现明显开放时间风险，但出行前仍建议确认官方信息。</p>
        </section>
        """

    rows = ""

    for item in risk_items[:8]:
        rows += f"""
        <tr>
            <td>第 {escape(str(item.get('day', '')))} 天</td>
            <td>{escape(str(item.get('period', '')))}</td>
            <td>{escape(str(item.get('place_name', '')))}</td>
            <td>{escape(str(item.get('risk_level', '')))}</td>
            <td>{escape(str(item.get('message', '')))}</td>
        </tr>
        """

    return f"""
    <section class="section">
        <h2>开放时间检查</h2>
        <p>{escape(str(summary.get('suggestion', '建议出行前确认官方开放时间。')))}</p>
        <table class="budget-table">
            <tr>
                <th>日期</th>
                <th>时段</th>
                <th>地点</th>
                <th>风险</th>
                <th>说明</th>
            </tr>
            {rows}
        </table>
    </section>
    """


def build_event_section(event_info, trip_data):
    """
    生成城市活动 HTML 区域。
    """
    if not event_info:
        return ""

    events = event_info.get("events", [])
    summary = event_info.get("summary", {})
    event_advice = trip_data.get("event_advice", "")

    if not events:
        return f"""
        <section class="section">
            <h2>城市活动与特殊事件</h2>
            <p>{escape(str(event_advice or summary.get('suggestion', '暂未查询到明确活动信息。')))}</p>
            <p class="note-text">{escape(str(event_info.get('note', '')))}</p>
        </section>
        """

    rows = ""

    for event in events[:8]:
        rows += f"""
        <tr>
            <td>{escape(str(event.get('date', '')))}</td>
            <td>{escape(str(event.get('time', '')))}</td>
            <td>{escape(str(event.get('name', '')))}</td>
            <td>{escape(str(event.get('venue', '')))}</td>
            <td>{escape(str(event.get('category', '')))}</td>
            <td>{escape(str(event.get('recommendation', '')))}</td>
        </tr>
        """

    return f"""
    <section class="section">
        <h2>城市活动与特殊事件</h2>
        <p>{escape(str(event_advice or summary.get('suggestion', '')))}</p>
        <table class="budget-table">
            <tr>
                <th>日期</th>
                <th>时间</th>
                <th>活动</th>
                <th>地点</th>
                <th>类型</th>
                <th>建议</th>
            </tr>
            {rows}
        </table>
        <p class="note-text">{escape(str(event_info.get('note', '')))}</p>
    </section>
    """


def build_html_report(
    trip_data,
    budget=None,
    location_info=None,
    weather_info=None,
    image_info=None,
    hotel_info=None,
    transport_info=None,
    opening_hours_info=None,
    event_info=None
):
    """
    根据 trip_data、budget、location_info、weather_info、image_info 生成 HTML 文本。
    """
    budget = budget or {}
    location_info = location_info or {}
    weather_info = weather_info or {}
    hotel_info = hotel_info or {}
    transport_info = transport_info or {}
    opening_hours_info = opening_hours_info or {}
    event_info = event_info or {}

    origin = trip_data.get("origin") or transport_info.get("origin")
    destination = trip_data.get("destination", "未知目的地")
    days = trip_data.get("days", "未知")
    preference = trip_data.get("preference", "未填写")
    pace = trip_data.get("pace", "适中")
    budget_level = trip_data.get("budget_level", "中")
    people = trip_data.get("people", budget.get("people", 1))
    travel_dates = trip_data.get("travel_dates", {})
    start_date = trip_data.get("start_date") or travel_dates.get("start_date")
    end_date = trip_data.get("end_date") or travel_dates.get("end_date")

    weather_summary = trip_data.get("weather_summary", "暂无天气摘要。")
    weather_adjustment = trip_data.get("weather_adjustment", "暂无天气适配说明。")
    route_strategy = trip_data.get("route_strategy", "暂无路线策略说明。")
    transport_advice = trip_data.get("transport_advice", "暂无交通建议。")
    intercity_transport_advice = trip_data.get("intercity_transport_advice", "暂无城际交通建议。")
    hotel_advice = trip_data.get("hotel_advice", "暂无住宿选址建议。")
    event_advice = trip_data.get("event_advice", "暂无城市活动建议。")
    backup_plan = trip_data.get("backup_plan", "暂无备选方案。")
    suitable_for = trip_data.get("suitable_for", "暂无适合人群说明。")
    advice = trip_data.get("advice", "暂无旅行建议。")
    edit_summary = trip_data.get("edit_summary")
    plan = trip_data.get("plan", [])

    if location_info.get("success"):
        location_block = build_info_list([
            ("标准地址", location_info.get("formatted_address")),
            ("省份", location_info.get("province")),
            ("城市", location_info.get("city")),
            ("行政区编码", location_info.get("adcode")),
            ("经度", location_info.get("longitude")),
            ("纬度", location_info.get("latitude"))
        ])
    else:
        location_block = f"<p>{escape(str(location_info.get('error', '暂无地图信息')))}</p>"

    if weather_info.get("success"):
        weather_items = [
            ("城市", weather_info.get("city")),
            ("天气模式", weather_info.get("mode", "live"))
        ]

        if weather_info.get("mode") == "forecast":
            for item in weather_info.get("forecasts", []):
                weather_items.append((
                    item.get("date"),
                    f"白天 {item.get('dayweather')} {item.get('daytemp')}℃，"
                    f"夜间 {item.get('nightweather')} {item.get('nighttemp')}℃"
                ))
        else:
            weather_items.extend([
                ("天气", weather_info.get("weather")),
                ("温度", f"{weather_info.get('temperature')}℃"),
                ("风向", weather_info.get("winddirection")),
                ("风力", weather_info.get("windpower")),
                ("湿度", f"{weather_info.get('humidity')}%")
            ])

        weather_items.append(("发布时间", weather_info.get("reporttime")))

        if weather_info.get("note"):
            weather_items.append(("说明", weather_info.get("note")))

        weather_block = build_info_list(weather_items)
    else:
        weather_note = weather_info.get("note")
        weather_block = f"<p>{escape(str(weather_info.get('error', '暂无天气信息')))}</p>"
        if weather_note:
            weather_block += f"<p>{escape(str(weather_note))}</p>"

    edit_summary_block = ""
    if edit_summary:
        edit_summary_block = f"""
        <section class="section highlight">
            <h2>本次修改说明</h2>
            <p>{escape(str(edit_summary))}</p>
        </section>
        """

    hotel_candidates = hotel_info.get("hotel_candidates", [])[:5]
    hotel_cards = ""

    for hotel in hotel_candidates:
        hotel_cards += f"""
        <div class="hotel-card">
            <h3>{escape(str(hotel.get('name', '酒店候选')))}</h3>
            <p><strong>地址：</strong>{escape(str(hotel.get('address', '暂无')))}</p>
            <p><strong>区域：</strong>{escape(str(hotel.get('district', '暂无')))}</p>
            <p><strong>平均距离：</strong>{escape(str(hotel.get('avg_distance_km', '暂无')))} km</p>
            <p><strong>最近景点：</strong>{escape(str(hotel.get('nearest_place', '暂无')))}</p>
            <p><strong>最远景点：</strong>{escape(str(hotel.get('farthest_place', '暂无')))}</p>
            <p><strong>推荐理由：</strong>{escape(str(hotel.get('reason', '暂无')))}</p>
        </div>
        """

    hotel_section = f"""
    <section class="section">
        <h2>住宿选址建议</h2>
        <p>{escape(str(hotel_advice))}</p>
        <p><strong>区域建议：</strong>{escape(str(hotel_info.get('area_suggestion', '暂无区域建议')))}</p>
        <div class="hotel-grid">
            {hotel_cards}
        </div>
        <p class="note-text">{escape(str(hotel_info.get('note', '')))}</p>
    </section>
    """

    recommendation = transport_info.get("recommendation", {})
    driving = transport_info.get("driving", {})
    transit = transport_info.get("transit", {})
    transport_section = f"""
    <section class="section">
        <h2>出发地到目的地交通建议</h2>
        <p><strong>出发地：</strong>{escape(str(origin or transport_info.get('origin', '未填写')))}</p>
        <p><strong>目的地：</strong>{escape(str(destination))}</p>
        <p><strong>推荐方式：</strong>{escape(str(recommendation.get('main_mode', '暂无')))}</p>
        <p><strong>推荐理由：</strong>{escape(str(recommendation.get('reason', intercity_transport_advice)))}</p>
        <p><strong>第一天安排建议：</strong>{escape(str(recommendation.get('first_day_advice', '')))}</p>
        <p><strong>驾车距离：</strong>{escape(str(driving.get('distance_km', '未知')))} km</p>
        <p><strong>驾车耗时：</strong>{escape(str(driving.get('duration_hour', '未知')))} 小时</p>
        <p><strong>公共交通耗时：</strong>{escape(str(transit.get('duration_hour', '未知')))} 小时</p>
        <p class="note-text">{escape(str(transport_info.get('note', '')))}</p>
    </section>
    """

    image_info = image_info or {}
    image_gallery_block = build_image_gallery(image_info)
    opening_hours_section = build_opening_hours_section(opening_hours_info)
    event_section = build_event_section(event_info, trip_data)
    day_images_map = {}

    for item in image_info.get("day_images", []):
        day_images_map[item.get("day")] = item.get("place_images", [])
        day_images_map[str(item.get("day"))] = item.get("place_images", [])

    plan_cards = ""
    for day_plan in plan:
        day = day_plan.get("day", "")
        date = day_plan.get("date")
        title = f"第 {day} 天（{date}）" if date else f"第 {day} 天"
        place_images = day_images_map.get(day, []) or day_images_map.get(str(day), [])
        image_cards_html = build_place_image_cards(place_images)
        plan_cards += f"""
        <div class="day-card">
            <h3>{escape(str(title))}</h3>
            <p><span>上午</span>{escape(str(day_plan.get('morning', '')))}</p>
            <p><span>下午</span>{escape(str(day_plan.get('afternoon', '')))}</p>
            <p><span>晚上</span>{escape(str(day_plan.get('evening', '')))}</p>
            <p><span>说明</span>{escape(str(day_plan.get('note', '')))}</p>
            <p><span>推荐理由</span>{escape(str(day_plan.get('reason', '')))}</p>
            {image_cards_html}
        </div>
        """

    html_text = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{escape(str(destination))}旅行计划</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif;
            background: #f4f6f8;
            color: #263238;
            line-height: 1.7;
        }}

        .container {{
            max-width: 980px;
            margin: 40px auto;
            padding: 0 24px 40px;
        }}

        .hero {{
            background: linear-gradient(135deg, #d8e6e7, #f2eadf);
            border-radius: 24px;
            padding: 36px;
            margin-bottom: 24px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        }}

        .hero h1 {{
            margin: 0 0 12px;
            font-size: 34px;
            color: #1f3a3d;
        }}

        .hero p {{
            margin: 4px 0;
            color: #546a6d;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 18px;
        }}

        .section {{
            background: #ffffff;
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 18px;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.06);
        }}

        .section h2 {{
            margin-top: 0;
            font-size: 22px;
            color: #264653;
            border-left: 5px solid #7aa6a1;
            padding-left: 12px;
        }}

        .highlight {{
            background: #fff7ed;
            border: 1px solid #f1c89a;
        }}

        ul {{
            padding-left: 20px;
        }}

        .tag-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 16px;
        }}

        .tag {{
            background: #e6eeee;
            color: #31575b;
            padding: 8px 14px;
            border-radius: 999px;
            font-size: 14px;
        }}

        .photo-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 16px;
        }}

        .day-photo-grid {{
            margin-top: 16px;
        }}

        .hotel-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 16px;
            margin-top: 16px;
        }}

        .hotel-card {{
            background: #f8faf9;
            border: 1px solid #dfe8e6;
            border-radius: 18px;
            padding: 18px;
        }}

        .hotel-card h3 {{
            margin-top: 0;
            color: #2f5d62;
        }}

        .note-text {{
            font-size: 13px;
            color: #78909c;
            margin-top: 12px;
        }}

        .photo-card {{
            background: #ffffff;
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid #dfe8e6;
        }}

        .photo-card img {{
            width: 100%;
            height: 180px;
            object-fit: cover;
            display: block;
        }}

        .photo-caption {{
            padding: 12px 14px;
            font-size: 13px;
            color: #546a6d;
        }}

        .photo-caption p {{
            margin: 4px 0;
        }}

        .photo-credit {{
            font-size: 12px;
            color: #78909c;
        }}

        .photo-query {{
            font-size: 12px;
            color: #4d7772;
        }}

        .photo-credit a {{
            color: #4d7772;
            text-decoration: none;
        }}

        .day-card {{
            background: #f8faf9;
            border: 1px solid #dfe8e6;
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 16px;
        }}

        .day-card h3 {{
            margin-top: 0;
            color: #2f5d62;
        }}

        .day-card span {{
            display: inline-block;
            min-width: 78px;
            font-weight: bold;
            color: #4d7772;
        }}

        .budget-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}

        .budget-table th,
        .budget-table td {{
            border-bottom: 1px solid #e3e8e6;
            padding: 12px;
            text-align: left;
        }}

        .budget-table th {{
            background: #eef5f4;
            color: #31575b;
        }}

        .footer {{
            text-align: center;
            color: #78909c;
            font-size: 14px;
            margin-top: 28px;
        }}

        @media (max-width: 720px) {{
            .grid,
            .photo-grid {{
                grid-template-columns: 1fr;
            }}

            .hotel-grid {{
                grid-template-columns: 1fr;
            }}

            .hero h1 {{
                font-size: 28px;
            }}
        }}

        @media print {{
            body {{
                background: #ffffff;
            }}

            .container {{
                margin: 0;
                max-width: none;
                padding: 0;
            }}

            .section,
            .hero,
            .day-card,
            .photo-card {{
                box-shadow: none;
                page-break-inside: avoid;
                break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <section class="hero">
            <h1>{escape(str(destination))}旅行计划</h1>
            <p>导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <div class="tag-list">
                <span class="tag">{escape(str(days))} 天</span>
                {f'<span class="tag">出行：{escape(str(start_date))} 至 {escape(str(end_date))}</span>' if start_date and end_date else ''}
                {f'<span class="tag">出发：{escape(str(origin))}</span>' if origin else ''}
                <span class="tag">{escape(str(people))} 人出行</span>
                <span class="tag">偏好：{escape(str(preference))}</span>
                <span class="tag">节奏：{escape(str(pace))}</span>
                <span class="tag">预算：{escape(str(budget_level))}</span>
            </div>
        </section>

        {image_gallery_block}
        {edit_summary_block}

        {transport_section}

        <div class="grid">
            <section class="section">
                <h2>目的地信息</h2>
                {location_block}
            </section>

            <section class="section">
                <h2>天气信息</h2>
                {weather_block}
            </section>
        </div>

        <section class="section">
            <h2>智能适配分析</h2>
            <p><strong>天气摘要：</strong>{escape(str(weather_summary))}</p>
            <p><strong>天气适配：</strong>{escape(str(weather_adjustment))}</p>
            <p><strong>路线策略：</strong>{escape(str(route_strategy))}</p>
            <p><strong>交通建议：</strong>{escape(str(transport_advice))}</p>
            <p><strong>城市活动建议：</strong>{escape(str(event_advice))}</p>
            <p><strong>雨天备选方案：</strong>{escape(str(backup_plan))}</p>
        </section>

        <section class="section">
            <h2>每日行程安排</h2>
            {plan_cards}
        </section>

        {event_section}
        {opening_hours_section}

        <section class="section">
            <h2>预算估算</h2>
            <table class="budget-table">
                <tr><th>项目</th><th>金额</th></tr>
                <tr><td>住宿费用</td><td>{escape(str(budget.get('hotel', 0)))} 元</td></tr>
                <tr><td>餐饮费用</td><td>{escape(str(budget.get('food', 0)))} 元</td></tr>
                <tr><td>交通费用</td><td>{escape(str(budget.get('transport', 0)))} 元</td></tr>
                <tr><td>门票费用</td><td>{escape(str(budget.get('ticket', 0)))} 元</td></tr>
                <tr><td>人均预算</td><td>{escape(str(budget.get('single_person_total', 0)))} 元</td></tr>
                <tr><td><strong>预计总预算</strong></td><td><strong>{escape(str(budget.get('total', 0)))} 元</strong></td></tr>
            </table>
        </section>

        {hotel_section}

        <section class="section">
            <h2>适合人群</h2>
            <p>{escape(str(suitable_for))}</p>
        </section>

        <section class="section">
            <h2>旅行建议</h2>
            <p>{escape(str(advice))}</p>
        </section>

        <div class="footer">
            智能旅行助手生成 · 请根据实际天气、交通和景区开放情况灵活调整
        </div>
    </div>
</body>
</html>
"""

    return html_text


def export_trip_to_pdf(
    trip_data,
    budget=None,
    location_info=None,
    weather_info=None,
    image_info=None,
    hotel_info=None,
    transport_info=None,
    opening_hours_info=None,
    event_info=None
):
    """
    将旅行计划导出为 PDF 文件。
    实现方式：先生成 HTML，再使用 Playwright 将 HTML 转换为 PDF。
    """
    ensure_export_dir()

    html_filename = build_export_filename(trip_data, suffix="html")
    pdf_filename = build_export_filename(trip_data, suffix="pdf")

    html_filepath = os.path.join(EXPORT_DIR, html_filename)
    pdf_filepath = os.path.join(EXPORT_DIR, pdf_filename)

    html_text = build_html_report(
        trip_data=trip_data,
        budget=budget,
        location_info=location_info,
        weather_info=weather_info,
        image_info=image_info,
        hotel_info=hotel_info,
        transport_info=transport_info,
        opening_hours_info=opening_hours_info,
        event_info=event_info
    )

    with open(html_filepath, "w", encoding="utf-8") as file:
        file.write(html_text)

    try:
        from playwright.sync_api import sync_playwright

        html_uri = Path(html_filepath).resolve().as_uri()

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(html_uri, wait_until="networkidle")
            page.pdf(
                path=pdf_filepath,
                format="A4",
                print_background=True,
                margin={
                    "top": "16mm",
                    "right": "14mm",
                    "bottom": "16mm",
                    "left": "14mm"
                }
            )
            browser.close()

        return pdf_filepath

    except ImportError:
        raise ImportError(
            "未安装 playwright。请先执行：pip install playwright，然后执行：playwright install chromium"
        )
