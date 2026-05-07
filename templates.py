# templates.py


def format_trip_plan(trip_data, budget, location_info=None, weather_info=None):
    """
    将大模型生成的旅行计划、预算信息、地图信息和天气信息格式化为命令行文本。
    """
    destination = trip_data.get("destination", "未知目的地")
    origin = trip_data.get("origin")
    days = trip_data.get("days", "未知")
    preference = trip_data.get("preference", "未填写")
    pace = trip_data.get("pace", "适中")
    budget_level = trip_data.get("budget_level", "中")
    people = trip_data.get("people", budget.get("people", 1))
    plan = trip_data.get("plan", [])
    travel_dates = trip_data.get("travel_dates", {})
    start_date = trip_data.get("start_date") or travel_dates.get("start_date")
    end_date = trip_data.get("end_date") or travel_dates.get("end_date")

    weather_summary = trip_data.get("weather_summary", "暂无天气摘要。")
    weather_adjustment = trip_data.get("weather_adjustment", "暂无天气适配说明。")
    route_strategy = trip_data.get("route_strategy", "暂无路线策略说明。")
    transport_advice = trip_data.get("transport_advice", "暂无交通建议。")
    intercity_transport_advice = trip_data.get("intercity_transport_advice")
    hotel_advice = trip_data.get("hotel_advice")
    event_advice = trip_data.get("event_advice")
    edit_summary = trip_data.get("edit_summary")

    suitable_for = trip_data.get("suitable_for", "适合希望获得基础旅行规划的用户。")
    advice = trip_data.get("advice", "建议根据实际天气、交通情况和个人体力灵活调整行程。")
    backup_plan = trip_data.get("backup_plan", "暂无备选方案。")

    result = []

    result.append("=" * 60)
    result.append("智能旅行助手 - Tool + LLM 增强命令行版")
    result.append("=" * 60)
    if origin:
        result.append(f"出发地：{origin}")
    result.append(f"目的地：{destination}")
    if start_date and end_date:
        result.append(f"出行日期：{start_date} 至 {end_date}")
    elif start_date:
        result.append(f"出行日期：{start_date}")
    result.append(f"旅行天数：{days} 天")
    result.append(f"旅行偏好：{preference}")
    result.append(f"旅行节奏：{pace}")
    result.append(f"预算档位：{budget_level}")
    result.append(f"出行人数：{people} 人")
    result.append("")

    result.append("一、目的地地图信息")
    result.append("-" * 60)
    if location_info and location_info.get("success"):
        result.append(f"标准地址：{location_info.get('formatted_address')}")
        result.append(f"省份：{location_info.get('province')}")
        result.append(f"城市：{location_info.get('city')}")
        result.append(f"行政区编码：{location_info.get('adcode')}")
        result.append(f"经度：{location_info.get('longitude')}")
        result.append(f"纬度：{location_info.get('latitude')}")
    else:
        error = location_info.get("error") if location_info else "未调用地图工具"
        result.append(f"地图信息查询失败：{error}")
    result.append("")

    result.append("二、目的地天气信息")
    result.append("-" * 60)
    if weather_info and weather_info.get("success"):
        result.append(f"城市：{weather_info.get('city')}")
        result.append(f"天气模式：{weather_info.get('mode', 'live')}")
        if weather_info.get("mode") == "forecast":
            for item in weather_info.get("forecasts", []):
                result.append(
                    f"{item.get('date')}：白天 {item.get('dayweather')} "
                    f"{item.get('daytemp')}℃，夜间 {item.get('nightweather')} "
                    f"{item.get('nighttemp')}℃"
                )
        else:
            result.append(f"天气：{weather_info.get('weather')}")
            result.append(f"温度：{weather_info.get('temperature')}℃")
            result.append(f"风向：{weather_info.get('winddirection')}")
            result.append(f"风力：{weather_info.get('windpower')}")
            result.append(f"湿度：{weather_info.get('humidity')}%")
        result.append(f"发布时间：{weather_info.get('reporttime')}")
        if weather_info.get("note"):
            result.append(f"说明：{weather_info.get('note')}")
    else:
        error = weather_info.get("error") if weather_info else "未调用天气工具"
        result.append(f"天气信息查询失败：{error}")
        if weather_info and weather_info.get("note"):
            result.append(f"说明：{weather_info.get('note')}")
    result.append("")

    result.append("三、智能适配分析")
    result.append("-" * 60)
    result.append(f"天气摘要：{weather_summary}")
    result.append(f"天气适配：{weather_adjustment}")
    result.append(f"路线策略：{route_strategy}")
    result.append(f"交通建议：{transport_advice}")
    result.append("")

    if intercity_transport_advice:
        result.append("出发地到目的地交通建议")
        result.append("-" * 60)
        result.append(intercity_transport_advice)
        result.append("")

    if hotel_advice:
        result.append("住宿选址建议")
        result.append("-" * 60)
        result.append(hotel_advice)
        result.append("")

    if event_advice:
        result.append("城市活动与特殊事件建议")
        result.append("-" * 60)
        result.append(event_advice)
        result.append("")

    result.append("四、每日行程安排")
    result.append("-" * 60)
    for day_plan in plan:
        date = day_plan.get("date")
        if date:
            result.append(f"第 {day_plan.get('day', '')} 天（{date}）")
        else:
            result.append(f"第 {day_plan.get('day', '')} 天")
        result.append(f"上午：{day_plan.get('morning', '')}")
        result.append(f"下午：{day_plan.get('afternoon', '')}")
        result.append(f"晚上：{day_plan.get('evening', '')}")
        result.append(f"说明：{day_plan.get('note', '')}")
        result.append(f"推荐理由：{day_plan.get('reason', '')}")
        result.append("")

    result.append("五、预算估算")
    result.append("-" * 60)
    result.append(f"住宿费用：{budget.get('hotel', 0)} 元")
    result.append(f"餐饮费用：{budget.get('food', 0)} 元")
    result.append(f"交通费用：{budget.get('transport', 0)} 元")
    result.append(f"门票费用：{budget.get('ticket', 0)} 元")
    result.append(f"人均预算：{budget.get('single_person_total', 0)} 元")
    result.append(f"预计总预算：{budget.get('total', 0)} 元")
    result.append("")

    result.append("六、适合人群")
    result.append("-" * 60)
    result.append(suitable_for)
    result.append("")

    result.append("七、旅行建议")
    result.append("-" * 60)
    result.append(advice)
    result.append("")

    result.append("八、备选方案")
    result.append("-" * 60)
    result.append(backup_plan)
    result.append("")

    if edit_summary:
        result.append("本次修改说明")
        result.append("-" * 60)
        result.append(edit_summary)
        result.append("")

    result.append("=" * 60)

    return "\n".join(result)
