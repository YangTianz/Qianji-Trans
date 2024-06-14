import argparse
import asyncio
import codecs
import json
import os
import re
import subprocess
import time

from functools import partial
from typing import Type  # noqa: F401

from ytzlib.tick_helper import ticker

from billing.bill_loader import AlipayBillLoader
from billing.bill_loader import WeChatBillLoader
from billing.bill_loader.base import Loader
from billing.const import HEADER
from billing.const import TranStatus
from billing.db import check_and_create_database
from billing.db import insert_transactions
from billing.db import load_transactions_from_db
from billing.file_utils import ensure_dir_exist
from billing.file_utils import scan_and_move
from billing.logger import logger
from billing.qianji.qianji import QianjiTransaction


def dump_db(output_dir: str) -> None:
    all_transactions = load_transactions_from_db()
    output = [t.dump() for t in all_transactions.values()]
    output.insert(0, HEADER)
    ensure_dir_exist(output_dir)
    with open(os.path.join(output_dir, "output.csv"), "wb") as f:
        b = bytes("\r\n".join(output), encoding="utf-8")
        f.write(codecs.BOM_UTF8 + b)


def load_rules_file(file_path: str) -> list:
    all_rules: list = []
    with open(file_path, "r", encoding="utf-8") as fp:
        try:
            all_rules = json.load(fp)
        except Exception:
            pass
    seen = set()
    unique_rules = []
    for rule in all_rules:
        rule_dump = json.dumps(rule)
        if rule_dump not in seen:
            seen.add(rule_dump)
            unique_rules.append(rule)
    unique_rules.sort(key=lambda rule: rule.get("order", 99))
    return unique_rules


def load_from_raw_bill(args: "BillingArgs", event: asyncio.Event) -> None:
    """从微信支付宝账单数据读取新产生的交易，写入数据库"""
    all_transactions = load_transactions_from_db()
    dump_db(args.output_path)
    raw_data_path = os.path.join(args.work_dir, "!raw_bill")
    ensure_dir_exist(raw_data_path)
    dump_path = os.path.join(args.work_dir, "archived", "raw_bills")
    ensure_dir_exist(dump_path)

    account_rules_list: list = load_rules_file(args.account_rules)
    classify_rules_list: list = load_rules_file(args.classify_rules)
    loaders = [
        WeChatBillLoader,
        AlipayBillLoader,
    ]  # type: list[Type[Loader]]
    new_transactions: dict[str, QianjiTransaction] = {}
    for loader_cls in loaders:
        loader: Loader = loader_cls(account_rules_list, classify_rules_list)

        def file_name_validator(
            file_name: str, regex_pattern: str = loader.file_regex
        ) -> bool:
            regex = re.compile(regex_pattern)
            return regex.match(file_name) is not None

        file_contents = scan_and_move(
            raw_data_path, dump_path, file_name_validator
        )
        for csv_file_contents in file_contents.values():
            transactions = loader.parse_file_content(
                csv_file_contents.decode(loader.encoding)
            )
            for transaction in transactions:
                tid = transaction.id
                if transaction.is_valid() and tid not in all_transactions:
                    new_transactions[tid] = transaction
    if new_transactions:
        logger.show(
            "[load transactions from wechat and alipay][new count=%s]"
            % len(new_transactions),
        )
        event.set()
        insert_transactions(list(new_transactions.values()), TranStatus.Raw)
        dump_db(args.output_path)
        all_transactions.update(new_transactions)


async def output_confirmed_data(
    args: "BillingArgs", event: asyncio.Event
) -> None:
    """将未分类交易输出到文件，等待用户确认"""
    dump_path = os.path.join(args.work_dir, "unconfirmed.csv")
    await event.wait()
    unconfirmed_t = load_transactions_from_db(TranStatus.Raw)
    if unconfirmed_t:
        output = [t.dump() for t in unconfirmed_t.values()]
        output.insert(0, HEADER)
        with open(dump_path, "wb") as f:
            b = bytes("\n".join(output), encoding="utf-8")
            f.write(codecs.BOM_UTF8 + b)
            logger.show(
                "[write unconfirmed transactions][count=%s]"
                % len(unconfirmed_t)
            )
    event.clear()


async def handle_confirmed_data(
    args: "BillingArgs", queue: asyncio.Queue
) -> None:
    """将已确认的数据入库"""
    input_path = os.path.join(args.work_dir, "confirmed")
    ensure_dir_exist(input_path)
    dump_path = os.path.join(args.work_dir, "archived", "confirmed")
    ensure_dir_exist(dump_path)

    def file_name_validator(file_name: str) -> bool:
        return file_name == "unconfirmed.csv"

    postfix = "-" + str(int(time.time()))
    contents = scan_and_move(
        input_path, dump_path, file_name_validator, postfix=postfix
    )
    for _, content in contents.items():
        confirmed = QianjiTransaction.load_from_file_content(
            content.decode("utf-8")
        )
        if confirmed:
            insert_transactions(
                list(confirmed.values()), TranStatus.Classified
            )
            dump_db(args.output_path)
            logger.show("[transactions confirmed][count=%s]" % len(confirmed))
            for t in confirmed.values():
                await queue.put(t)


async def finial_adb_output(args: "BillingArgs", queue: asyncio.Queue) -> None:
    transaction: QianjiTransaction = await queue.get()
    adb_cmd = transaction.dump_to_adb_command()
    insert_transactions(
        [
            transaction,
        ],
        TranStatus.Written,
    )
    dump_db(args.output_path)
    logger.debug(adb_cmd)
    subprocess.run(adb_cmd, shell=True)


async def main() -> None:
    args = parse_arguments()
    ensure_dir_exist(args.work_dir)
    logger.init(os.path.join(args.work_dir, "log.txt"))
    check_and_create_database()
    unconfirmed_transaction_event = asyncio.Event()
    func = partial(load_from_raw_bill, args, unconfirmed_transaction_event)
    ticker.repeat_call(func, 3.0)
    func = partial(output_confirmed_data, args, unconfirmed_transaction_event)  # type: ignore
    ticker.repeat_call(func, 1.0)
    uninsert_transaction_list: asyncio.Queue = asyncio.Queue()
    func = partial(handle_confirmed_data, args, uninsert_transaction_list)  # type: ignore
    ticker.repeat_call(func, 3.0)
    func = partial(finial_adb_output, args, uninsert_transaction_list)  # type: ignore
    ticker.repeat_call(func, 4.0)
    await asyncio.gather(ticker.start())


class BillingArgs(argparse.Namespace):
    def __init__(self) -> None:
        self.account_rules: str = ""
        self.classify_rules: str = ""
        self.work_dir: str = ""
        self.output_path: str = "output"


def parse_arguments() -> BillingArgs:
    # 创建 ArgumentParser 对象
    parser = argparse.ArgumentParser(
        description="Parse command line arguments."
    )
    parser.add_argument(
        "--work-dir", required=True, type=str, help="Working directory path."
    )
    parser.add_argument(
        "--account-rules",
        required=True,
        type=str,
        help="Path to the account rules file.",
    )
    parser.add_argument(
        "--classify-rules",
        required=True,
        type=str,
        help="Path to the category rules file.",
    )
    parser.add_argument(
        "--output-path",
        default="output",
        type=str,
        help="Path to the output CSV file.",
    )
    args = parser.parse_args(namespace=BillingArgs())
    args.account_rules
    return args


if __name__ == "__main__":
    asyncio.run(main())
