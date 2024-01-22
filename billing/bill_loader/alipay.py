import datetime
import re

from collections import defaultdict
from typing import Optional

from billing.const import TransactionType
from billing.const import TransactonFlag
from billing.logger import logger
from billing.qianji.qianji import QianjiTransaction

from .base import Loader


class AlipayBillLoader(Loader):
    def __init__(
        self,
        account_rules: list[dict],
        classify_rules: list[dict],
    ) -> None:
        super(AlipayBillLoader, self).__init__(
            account_rules, classify_rules
        )
        self._closed_order: dict = {}
        self._refund_cost_dict: dict = defaultdict(float)
        self._refund_order_data: dict = {}

    @property
    def name(self) -> str:
        return "alipay"

    @property
    def file_regex(self) -> str:
        return r"alipay_record_\d{8}_\d{6}\.csv"

    @property
    def encoding(self) -> str:
        return "GBK"

    def _parse_trade_time(self, text: str) -> int:
        pattern = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"
        match = re.match(pattern, text)
        if not match:
            return 0
        date_obj = datetime.datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        timestamp = int(date_obj.timestamp())
        return timestamp

    def _parse_type(self, line_data: list[str]) -> TransactionType:
        if line_data[5] == "收入":
            type_ = TransactionType.Income
        elif line_data[5] == "不计收支":
            type_ = TransactionType.Transfer
        else:
            type_ = TransactionType.Expense
        return type_

    def _parse_cost(self, line_data: list[str]) -> float:
        cost = float(line_data[6].strip())
        return cost

    def _get_account_parse_data(self, line_data: list[str]) -> dict:
        return {
            "account_text": line_data[7]
        }

    def _get_classify_parse_data(self, line_data: list[str]) -> dict:
        return {
            "type_": line_data[1],
            "counterparty": line_data[2],
            "merchandise": line_data[4],
        }

    def _parse_trade_record(
        self,
        type_: TransactionType,
        trade_time: int,
        cost: float,
        acc_from: str,
        classify: str,
        line_data: list[str],
    ) -> Optional[QianjiTransaction]:
        shouzhi = line_data[5]
        trade_status = line_data[8]
        merchant_order_number = line_data[10].strip()

        acc_to = ""
        remark_postfix = self.AUTO_CLASSIFY_MARK if classify else ""
        transaction = QianjiTransaction(
            trade_time,
            classify,
            type_,
            cost,
            acc_from,
            acc_to,
            TransactonFlag.Empty,
            self._get_remark(line_data) + remark_postfix,
            extra_info={"merchant_order_number": merchant_order_number},
            tid=line_data[9].strip(),
        )

        if trade_status == "交易关闭":
            self._closed_order[merchant_order_number] = transaction

        # 不计收支一般是余额宝收入和退货退款
        if shouzhi == "不计收支":
            if trade_status == "退款成功":
                self._refund_cost_dict[merchant_order_number] += cost
                self._refund_order_data[merchant_order_number] = line_data
            return None

        return transaction

    def _get_remark(self, line_data: list[str]) -> str:
        name = self.name
        counterparty = line_data[2]
        merchandise = line_data[4]
        transaction_id = line_data[9].strip()
        ret = f"{name}--{counterparty}--{merchandise}--[TID:{transaction_id}]"
        return ret

    def _post_process(
        self, transaction_records: list[QianjiTransaction]
    ) -> list[QianjiTransaction]:
        for transaction in transaction_records:
            order_number = transaction.extra_info["merchant_order_number"]
            if order_number in self._refund_cost_dict:
                transaction.refund(self._refund_cost_dict[order_number])
                del self._refund_cost_dict[order_number]

        for order_number in list(self._refund_cost_dict.keys()):
            if order_number in self._closed_order:
                del self._refund_cost_dict[order_number]

        for order_number in list(self._refund_cost_dict.keys()):
            data = self._refund_order_data[order_number]
            logger.warning(
                "            部分退款交易未能正确识别导致未录入，原始数据：%s"
                % data
            )

        self.clear_cache()
        return list(filter(lambda t: t.is_valid(), transaction_records))

    def clear_cache(self) -> None:
        self._closed_order = {}
        self._refund_cost_dict = defaultdict(float)
        self._refund_order_data = {}
