from enum import Enum
from typing import Type
from typing import TypeVar


HEADER = "时间,分类,类型,金额,账户1,账户2,备注,账单标记,账单图片"


T = TypeVar("T", bound="Enum")


def safe_get_enum(enum_class: Type[T], value: str) -> T:
    try:
        ret = enum_class(value)
    except ValueError:
        ret = next(iter(enum_class.__members__.values()))
    return ret


class TransactionType(Enum):
    Expense = "支出"
    Income = "收入"
    Transfer = "转账"
    Repayment = "还款"
    Reimbursement = "报销"


class TransactonFlag(Enum):
    Empty = ""
    NC = "不计收支"
    NB = "不计预算"
    NBC = "不计收支&预算"


class CurrencyType(Enum):
    CNY = "CNY"
    JPY = "JPY"
    USD = "USD"


class AccountType(Enum):
    DebtCard = "借记卡"
    CreditCard = "信用卡"
    Investment = "投资"


class TranStatus(Enum):
    Raw = 0
    Classified = 1
    Written = 2
