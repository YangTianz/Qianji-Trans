from typing import Optional

from billing.checker import check_rules
from billing.const import TransactionType
from billing.qianji.qianji import QianjiTransaction


class Loader:
    AUTO_CLASSIFY_MARK = "[auto]"

    def __init__(
        self,
        account_rules: list[dict],
        classify_rules: list[dict],
    ):
        self._account_rules: list[dict] = account_rules
        self._classify_rules: list[dict] = classify_rules

    @property
    def name(self) -> str:
        return "loader"

    @property
    def file_regex(self) -> str:
        return ""

    @property
    def encoding(self) -> str:
        return "utf-8"

    def _parse_trade_time(self, text: str) -> int:
        """将日期字符串转化为时间戳，不合法的返回 0"""
        raise NotImplementedError

    def _parse_type(self, line_data: list[str]) -> TransactionType:
        """根据行数据获取交易类型"""
        raise NotImplementedError

    def _parse_cost(self, line_data: list[str]) -> float:
        """根据行数据获取交易金额"""
        raise NotImplementedError

    def _parse_account_from(
        self, line_data: list[str], type_: TransactionType
    ) -> str:
        """根据给定规则获取资金来源/进入的账户名"""
        acc_from_core_data = self._get_account_parse_data(line_data)
        acc_from_core_data["loader"] = self.name
        acc_from_core_data["is_income"] = type_ == TransactionType.Income
        acc_from_core_data["is_expense"] = type_ == TransactionType.Expense
        return check_rules(acc_from_core_data, self._account_rules)

    def _get_account_parse_data(self, line_data: list[str]) -> dict:
        raise NotImplementedError

    def _parse_classify(
        self, line_data: list[str], type_: TransactionType
    ) -> str:
        """根据给定规则获取交易分类"""
        classify_cor_data = self._get_classify_parse_data(line_data)
        classify_cor_data["loader"] = self.name
        classify_cor_data["is_income"] = type_ == TransactionType.Income
        classify_cor_data["is_expense"] = type_ == TransactionType.Expense
        return check_rules(classify_cor_data, self._classify_rules)

    def _get_classify_parse_data(self, line_data: list[str]) -> dict:
        raise NotImplementedError

    def parse_file_content(self, file_content: str) -> list[QianjiTransaction]:
        ret = []
        for line in file_content.splitlines():
            record = self._parse_line(line)
            if record:
                ret.append(record)
        return self._post_process(ret)

    def _parse_line(self, line: str) -> Optional[QianjiTransaction]:
        line_data = line.strip().split(",")
        trade_time = self._parse_trade_time(line_data[0])
        if not trade_time:
            return None
        type_ = self._parse_type(line_data)
        cost = self._parse_cost(line_data)
        acc_from = self._parse_account_from(line_data, type_)
        classify = self._parse_classify(line_data, type_)
        record = self._parse_trade_record(
            type_, trade_time, cost, acc_from, classify, line_data
        )
        return record

    def _get_remark(self, line_data: list[str]) -> str:
        return self.name

    def _parse_trade_record(
        self,
        type_: TransactionType,
        trade_time: int,
        cost: float,
        acc_from: str,
        classify: str,
        line_data: list[str],
    ) -> Optional[QianjiTransaction]:
        """生成交易数据"""
        raise NotImplementedError

    def _post_process(
        self, transaction_records: list[QianjiTransaction]
    ) -> list[QianjiTransaction]:
        return transaction_records
