# menu.py
from date_utils import validate_date_format


def get_positive_int(prompt):
    """
    获取一个正整数输入。
    """
    while True:
        value = input(prompt)
        try:
            number = int(value)
            if number > 0:
                return number
            print("请输入大于 0 的数字。")
        except ValueError:
            print("请输入有效的整数。")


def get_choice(prompt, choices, default):
    """
    获取限定选项输入。
    如果用户输入为空或不在选项中，则使用默认值。
    """
    value = input(prompt).strip()

    if value in choices:
        return value

    print(f"输入无效，已默认设置为：{default}")
    return default


def get_date_input(prompt):
    """
    获取 YYYY-MM-DD 格式日期。
    """
    while True:
        value = input(prompt).strip()

        if validate_date_format(value):
            return value

        print("日期格式不正确，请按 YYYY-MM-DD 输入，例如 2026-05-01。")


def show_home_menu():
    """
    显示首页菜单。
    """
    print()
    print("=" * 60)
    print("欢迎使用智能旅行助手")
    print("=" * 60)
    print("1. 创建新行程")
    print("2. 读取已有行程")
    print("3. 退出程序")

    return input("请输入选项编号：").strip()


def show_trip_action_menu():
    """
    显示当前行程操作菜单。
    """
    print()
    print("当前行程操作：")
    print("1. 修改当前行程")
    print("2. 恢复上一版行程")
    print("3. 查看当前记忆")
    print("4. 保存当前行程")
    print("5. 查看并读取已保存行程")
    print("6. 导出 Markdown 报告")
    print("7. 导出 HTML 报告")
    print("8. 导出 PDF 报告")
    print("9. 返回首页")
    print("10. 退出程序")

    return input("请输入选项编号：").strip()


def input_trip_requirements():
    """
    输入创建新行程所需的基本信息。
    """
    print()
    print("开始创建新行程")
    print("=" * 60)

    origin = input("请输入出发地，例如 北京 / 北京南站 / 北京市：").strip()
    destination = input("请输入目的地：").strip()
    start_date = get_date_input("请输入计划出行日期，例如 2026-05-01：")
    days = get_positive_int("请输入旅行天数：")
    people = get_positive_int("请输入出行人数：")

    preference = input(
        "请输入旅行偏好，例如 自然风光 / 历史文化 / 美食 / 购物 / 拍照："
    ).strip()

    pace = get_choice(
        prompt="请输入旅行节奏，紧凑 / 适中 / 轻松：",
        choices=["紧凑", "适中", "轻松"],
        default="适中"
    )

    budget_level = get_choice(
        prompt="请输入预算档位，低 / 中 / 高：",
        choices=["低", "中", "高"],
        default="中"
    )

    if not destination:
        destination = "目标城市"

    if not origin:
        origin = "未填写"

    if not preference:
        preference = "综合体验"

    return {
        "origin": origin,
        "destination": destination,
        "start_date": start_date,
        "days": days,
        "people": people,
        "preference": preference,
        "pace": pace,
        "budget_level": budget_level
    }
