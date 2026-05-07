# tool_executor.py

from tools.tool_registry import run_tool


def resolve_argument_value(value, tool_results):
    """
    解析工具参数中的占位符。
    例如：
    "{{map_tool.adcode}}" 会被替换为 map_tool 结果中的 adcode。
    "{{poi_tool}}" 会被替换为整个 poi_tool 的结果。
    """
    if not isinstance(value, str):
        return value

    value = value.strip()

    if not (value.startswith("{{") and value.endswith("}}")):
        return value

    placeholder = value[2:-2].strip()

    if "." not in placeholder:
        return tool_results.get(placeholder, value)

    tool_name, field_name = placeholder.split(".", 1)
    tool_result = tool_results.get(tool_name, {})

    return tool_result.get(field_name)


def resolve_arguments(arguments, tool_results):
    """
    解析一个工具的全部参数。
    """
    resolved = {}

    for key, value in arguments.items():
        resolved[key] = resolve_argument_value(value, tool_results)

    return resolved


def execute_tool_plan(tool_plan):
    """
    执行大模型生成的工具调用计划。
    """
    tool_calls = tool_plan.get("tool_calls", [])
    tool_results = {}
    execution_logs = []

    for call in tool_calls:
        tool_name = call.get("tool_name")
        arguments = call.get("arguments", {})
        reason = call.get("reason", "")

        resolved_arguments = resolve_arguments(arguments, tool_results)
        result = run_tool(tool_name, **resolved_arguments)
        tool_results[tool_name] = result

        execution_logs.append({
            "tool_name": tool_name,
            "reason": reason,
            "arguments": resolved_arguments,
            "result": result
        })

    return {
        "tool_results": tool_results,
        "execution_logs": execution_logs
    }
