import re

from datetime import datetime
from typing import Optional
from typing import Type

from billing.const import TransactionType
from billing.const import TransactonFlag


class QianjiTransaction:
    def __init__(
        self,
        time: int,
        classify: str,
        type_: TransactionType,
        cost: float,
        acc_from: str,
        acc_to: str,
        flag: TransactonFlag,
        remark: str = "",
        extra_info: Optional[dict] = None,
        tid: Optional[str] = None,
    ):
        self._tid: str = tid if tid else self._get_tid_from_remark(remark)
        # 消费时间
        self._time: int = int(time)
        # 所属种类此处如果有二级分类，填写二级分类，如果没有二级分类，
        # 则填写一级分类，分类如果不填写，则默认为 其它
        self._classify: str = classify
        # 账单类型
        self._type: TransactionType = type_
        # 账单对应金额
        self._cost: float = round(cost, 2)
        # 收入或支出关联的账户，或者是转账账单的转出账户
        self._acc_from: str = acc_from
        # 只对转账账单生效
        self._acc_to: str = acc_to
        # 备注
        self._remark: str = remark
        # 标记
        self._flag: TransactonFlag = flag
        # ？
        self._img = ""
        self.status = 0

        if extra_info is None:
            extra_info = {}
        self._extra_info = extra_info

    @property
    def id(self) -> str:
        return self._tid

    @property
    def time(self) -> int:
        return self._time

    @property
    def extra_info(self) -> dict:
        return self._extra_info

    @property
    def classify(self) -> str:
        return self._classify

    def refund(self, refund: float) -> None:
        self._cost = round(self._cost - refund, 2)

    def is_valid(self) -> bool:
        if self._cost == 0:
            return False

        return True

    def dump_to_db(self) -> str:
        ret = (
            f'"{self.id}", {self.time}, "{self._classify}", '
            f'"{self._type.value}", {self._cost}, "{self._acc_from}", '
            f'"{self._acc_to}", "{self._remark}", '
            f'"{self._flag.value}"'
        )
        return ret

    def dump(self) -> str:
        return ",".join(
            [
                datetime.fromtimestamp(self._time).strftime(
                    "%Y/%m/%d %H:%M:%S"
                ),
                self._classify,
                self._type.value,
                str(round(self._cost, 2)),
                self._acc_from,
                self._acc_to,
                self._remark,
                self._flag.value,
                self._img,
            ]
        )

    def dump_to_api(self) -> str:
        time = datetime.fromtimestamp(self._time).strftime("%Y-%m-%d %H:%M:%S")
        cost = str(round(self._cost, 2))
        if self._type == TransactionType.Expense:
            type_ = 0
        elif self._type == TransactionType.Income:
            type_ = 1
        elif self._type == TransactionType.Transfer:
            type_ = 2
        else:
            return ""
        text = (
            f"qianji://publicapi/addbill?&type={type_}&money={cost}&"
            f"time={time}&remark={self._remark}&catename={self.classify}"
            f"&accountname={self._acc_from}&bookname=日常账本"
        )
        if self._type == TransactionType.Transfer:
            text += f"&accountname2={self._acc_to}"
        return text

    def dump_to_adb_command(self) -> str:
        text = self.dump_to_api()
        cmd = (
            "adb shell am start -a android.intent.action.VIEW " f'"""{text}"""'
        )
        return cmd

    @classmethod
    def load_from_file_content(
        cls: Type["QianjiTransaction"], file_content: str
    ) -> dict[str, "QianjiTransaction"]:
        ret = {}
        for line in file_content.splitlines()[1:]:
            line_data = line.split(",")
            datetime_obj = datetime.strptime(line_data[0], "%Y/%m/%d %H:%M:%S")
            ts = int(datetime.timestamp(datetime_obj))
            flag = (
                TransactonFlag(line_data[7])
                if line_data[7]
                else TransactonFlag.Empty
            )
            t = QianjiTransaction(
                ts,
                line_data[1],
                TransactionType(line_data[2]),
                float(line_data[3]),
                line_data[4],
                line_data[5],
                flag,
                line_data[6],
            )
            ret[t.id] = t
        return ret

    @classmethod
    def load_from_db(cls, row: list) -> "QianjiTransaction":
        t = QianjiTransaction(
            row[1],
            row[2],
            TransactionType(row[3]),
            row[4],
            row[5],
            row[6],
            TransactonFlag(row[8]),
            row[7],
            tid=row[0],
        )
        t.status = row[-1]
        return t

    def _get_tid_from_remark(self, remark: str) -> str:
        pattern = r"\[TID:(.*?)\]"
        match = re.search(pattern, remark)
        tid = match.group(1)  # type: ignore
        return tid
