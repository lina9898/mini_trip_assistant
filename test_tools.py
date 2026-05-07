from tools.budget_tool import estimate_budget
from tools.map_tool import get_location
from tools.weather_tool import get_weather_by_adcode


budget = estimate_budget(days=3, budget_level="中", people=2)
print("预算工具结果：")
print(budget)

location = get_location("杭州")
print("地图工具结果：")
print(location)

if location.get("success"):
    weather = get_weather_by_adcode(location.get("adcode"))
    print("天气工具结果：")
    print(weather)