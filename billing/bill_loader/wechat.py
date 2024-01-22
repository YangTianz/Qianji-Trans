import datetime
import re

from typing import Optional

from billing.const import TransactionType
from billing.const import TransactonFlag
from billing.logger import logger
from billing.qianji.qianji import QianjiTransaction

from .base import Loader


class WeChatBillLoader(Loader):
    @property
    def name(self) -> str:
        return "wechat"

    @property
    def file_regex(self) -> str:
        return r"微信支付账单\((\d{8}-\d{8})\)\.csv"

    def _parse_trade_time(self, text: str) -> int:
        pattern = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"
        match = re.match(pattern, text)
        if not match:
            return 0
        date_obj = datetime.datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        timestamp = int(date_obj.timestamp())
        return timestamp

    def _parse_type(self, line_data: list[str]) -> TransactionType:
        if line_data[4] == "收入":
            type_ = TransactionType.Income
        elif line_data[4] == "支出":
            type_ = TransactionType.Expense
        elif line_data[4] == "/":
            type_ = TransactionType.Transfer
        else:
            type_ = TransactionType.Transfer
        return type_

    def _parse_cost(self, line_data: list[str]) -> float:
        cost = float(line_data[5].strip()[1:])
        return cost

    def _get_account_parse_data(self, line_data: list[str]) -> dict:
        return {
            "account_text": line_data[6],
            "status_wechat": line_data[7],
        }

    def _get_classify_parse_data(self, line_data: list[str]) -> dict:
        return {
            "type_": line_data[1],
            "counterparty": line_data[2],
            "merchandise": line_data[3],
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
        acc_to = ""

        # 判断一下特殊情况
        trade_status = line_data[7]
        # 全额退款，不需要记录
        if trade_status in ["已全额退款", "对方已退还"]:
            return None
        # 这个有可能是部分交易退款，比如买菜缺斤少两退款、点咖啡退款
        elif type_ == TransactionType.Income and "已退款" in trade_status:
            # 这里直接返回是因为这样的退款直接在原来的支出订单减掉退款金额即可
            return None
        # 微信提现
        if type_ == TransactionType.Transfer and "提现已到账" in trade_status:
            acc_to = acc_from
            acc_from = "微信"

        if type_ == TransactionType.Income and not acc_from:
            logger.info(
                "未知收入去向，已以默认值(微信)记录，原始数据：%s"
                % str(line_data)
            )
            acc_from = "微信"

        # 与上面部分交易退款的逻辑相对应，在这里直接减去退款金额
        if type_ == TransactionType.Expense and "已退款" in trade_status:
            match = re.search(r"￥(\d+(\.\d{1,2})?)", trade_status)
            if match:
                refund = float(match.group(1))
            else:
                refund = 0
                logger.error(
                    "读取微信退款金额失败！！！原始数据：%s" % str(line_data)
                )
            cost -= refund

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
            tid=line_data[8].strip()
        )
        return transaction

    def _get_remark(self, line_data: list[str]) -> str:
        name = self.name
        counterparty = line_data[2]
        merchandise = line_data[3][1:-1]
        transaction_id = line_data[8].strip()
        ret = f"{name}--{counterparty}--{merchandise}--[TID:{transaction_id}]"
        return ret
