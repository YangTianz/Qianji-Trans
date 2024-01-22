import os
import sqlite3

from typing import Optional

from billing.const import TranStatus
from billing.qianji.qianji import QianjiTransaction


DBNAME = "mydatabase.db"


def create_database() -> None:
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE transactions (
            id TEXT PRIMARY KEY,
            time INTEGER NOT NULL,
            classify TEXT NOT NULL,
            type TEXT NOT NULL,
            cost REAL NOT NULL,
            acc_from TEXT NOT NULL,
            acc_to TEXT,
            remark TEXT,
            flag TEXT,
            pic TEXT,
            status INTEGER
        );
    """
    )
    conn.commit()
    conn.close()


def check_and_create_database() -> None:
    # 检查数据库文件是否存在
    if not os.path.exists(DBNAME):
        create_database()
        print("数据库已创建")
    else:
        print("数据库已存在，无需再次创建")


def insert_transactions(
    all_transactions: list[QianjiTransaction], status: TranStatus
) -> None:
    sql = """
    INSERT INTO transactions
        (id, time, classify, type, cost, acc_from, acc_to, remark, flag, status)
    VALUES
        (%s, %s)
    ON CONFLICT(id) DO UPDATE SET
        status = EXCLUDED.status,
        cost = EXCLUDED.cost,
        classify = EXCLUDED.classify,
        remark = EXCLUDED.remark
    """
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    for transaction in all_transactions:
        cursor.execute(sql % (transaction.dump_to_db(), status.value))
    conn.commit()
    conn.close()


def load_transactions_from_db(
    status: Optional[TranStatus] = None,
) -> dict[str, QianjiTransaction]:
    if status:
        where = "where status = %s" % status.value
    else:
        where = ""
    sql = f"""
    SELECT * FROM transactions {where} ORDER BY time DESC
    """
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    cursor.execute(sql)
    # 获取所有行
    rows = cursor.fetchall()

    ret = {}
    # 打印结果
    for row in rows:
        transaction = QianjiTransaction.load_from_db(row)
        ret[transaction.id] = transaction

    # 关闭游标和连接
    cursor.close()
    conn.close()
    return ret
