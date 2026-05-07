# app.py

from menu import show_home_menu, show_trip_action_menu, input_trip_requirements
from memory_manager import restore_previous_version, print_memory
from storage import mark_project_dirty
from trip_service import (
    create_project,
    load_project_flow,
    edit_project,
    save_current_project,
    export_current_project,
    print_project
)


def run_trip_action_menu(project_data):
    """
    当前行程操作菜单。
    """
    while True:
        choice = show_trip_action_menu()

        if choice == "1":
            project_data = edit_project(project_data)

        elif choice == "2":
            project_data, result = restore_previous_version(project_data)
            print(result["message"])

            if result.get("success"):
                project_data = mark_project_dirty(project_data)
                print_project(project_data)

        elif choice == "3":
            print_memory(project_data)

        elif choice == "4":
            project_data = save_current_project(project_data)

        elif choice == "5":
            loaded_project_data = load_project_flow()

            if loaded_project_data:
                project_data = loaded_project_data

        elif choice == "6":
            project_data = export_current_project(project_data, export_type="markdown")

        elif choice == "7":
            project_data = export_current_project(project_data, export_type="html")

        elif choice == "8":
            project_data = export_current_project(project_data, export_type="pdf")

        elif choice == "9":
            print("已返回首页。")
            return "home"

        elif choice == "10":
            print("行程规划已完成。")
            return "exit"

        else:
            print("无效选项，请重新输入。")


def run_app():
    """
    应用主入口。
    """
    while True:
        choice = show_home_menu()

        if choice == "1":
            requirements = input_trip_requirements()
            project_data = create_project(requirements)

            if project_data:
                result = run_trip_action_menu(project_data)

                if result == "exit":
                    break

        elif choice == "2":
            project_data = load_project_flow()

            if project_data:
                result = run_trip_action_menu(project_data)

                if result == "exit":
                    break

        elif choice == "3":
            print("已退出智能旅行助手。")
            break

        else:
            print("无效选项，请重新输入。")
