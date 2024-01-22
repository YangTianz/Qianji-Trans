from enum import Enum
from typing import Any


class Operator(Enum):
    NotInclude = "not in"
    Include = "in"
    Equal = "=="
    Is = "is"


def check_rules(data_dict: dict[str, Any], rule_list: list[dict]) -> str:
    for rule in rule_list:
        conditions = rule["conditions"]
        output_id = rule["output_id"]

        # 对于每个规则，检查是否所有条件都满足
        if all(
            check_condition(data_dict[condition["field_to_check"]], condition)
            for condition in conditions
        ):
            return output_id

    # 如果没有任何规则匹配，则返回默认值（例如，可以返回一个默认的 output_id 或者 None）
    return ""


def check_condition(value: Any, condition: dict) -> bool:
    operator = condition["operator"]
    expect_value = condition["expect_value"]
    if isinstance(value, str):
        value = value.lower()
    if isinstance(expect_value, str):
        expect_value = expect_value.lower()
    if operator == Operator.Include.value and expect_value in value:
        return True
    elif operator == Operator.NotInclude.value and expect_value not in value:
        return True
    elif operator == Operator.Equal.value and value.strip() == expect_value:
        return True
    elif operator == Operator.Is.value and value is expect_value:
        return True

    return False
