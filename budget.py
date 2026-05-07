# budget.py

def estimate_budget(days, budget_level, people):
    """
    根据旅行天数、预算档位和出行人数，估算旅行预算。

    参数：
    days: 旅行天数
    budget_level: 预算档位，可选：低、中、高
    people: 出行人数

    返回：
    一个预算明细字典
    """

    if budget_level == "低":
        hotel_per_day = 200
        food_per_day = 100
        transport_per_day = 50
        ticket_per_day = 80
    elif budget_level == "高":
        hotel_per_day = 800
        food_per_day = 300
        transport_per_day = 150
        ticket_per_day = 200
    else:
        hotel_per_day = 400
        food_per_day = 180
        transport_per_day = 80
        ticket_per_day = 120

    hotel_total = hotel_per_day * max(days - 1, 1)
    food_total = food_per_day * days
    transport_total = transport_per_day * days
    ticket_total = ticket_per_day * days

    single_person_total = hotel_total + food_total + transport_total + ticket_total
    total = single_person_total * people

    return {
        "people": people,
        "hotel": hotel_total * people,
        "food": food_total * people,
        "transport": transport_total * people,
        "ticket": ticket_total * people,
        "single_person_total": single_person_total,
        "total": total
    }