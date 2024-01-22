
import pytest

from billing.bill_loader import WeChatBillLoader
from billing.const import TransactionType


@pytest.fixture(scope="module")
def wechat_loader(account_rules_list, classify_rules_list):
    return WeChatBillLoader(account_rules_list, classify_rules_list)


def test_wechat_expense(wechat_loader: WeChatBillLoader) -> None:
    test_data = '2023-03-08 21:34:36,商户消费,麦当劳,"麦当劳",支出,¥13.90,招商银行(1908),支付成功,4200001754202303085118818875	,12553692042802585600	,"/"'
    line_data = test_data.split(",")
    assert wechat_loader._parse_cost(line_data) == 13.9
    assert wechat_loader._parse_type(line_data) == TransactionType.Expense
    type_ = wechat_loader._parse_type(line_data)
    assert wechat_loader._parse_account_from(line_data, type_) == "招行信用卡(0638)"
    assert wechat_loader._parse_classify(line_data, type_) == "吃饭"


def test_wechat_expense2(wechat_loader: WeChatBillLoader) -> None:
    test_data = '2023-09-09 18:59:30,商户消费,小鹏智慧充电,"小鹏汽车|充电",支出,¥36.54,招商银行(0638),支付成功,4200001901202309093803047044	,rkk_zHvpOPy_1e4BGfcHIzxxxxxKAvpx	,"/"'
    line_data = test_data.split(",")
    assert wechat_loader._parse_cost(line_data) == 36.54
    assert wechat_loader._parse_type(line_data) == TransactionType.Expense
    type_ = wechat_loader._parse_type(line_data)
    assert wechat_loader._parse_account_from(line_data, type_) == "招行信用卡(0638)"
    assert wechat_loader._parse_classify(line_data, type_) == "充电费"


def test_wechat_income(wechat_loader: WeChatBillLoader) -> None:
    test_data = '2023-09-05 14:10:57,群收款,xxx,"/",收入,¥17.75,/,已存入零钱,1000049501230905024203390023801596874984	,/	,"/"'
    line_data = test_data.split(",")
    assert wechat_loader._parse_cost(line_data) == 17.75
    assert wechat_loader._parse_type(line_data) == TransactionType.Income
    type_ = wechat_loader._parse_type(line_data)
    assert wechat_loader._parse_account_from(line_data, type_) == "微信"
    assert wechat_loader._parse_classify(line_data, type_) == "拼单回流"


def test_wechat_refund(wechat_loader: WeChatBillLoader) -> None:
    test_data = '2023-07-11 14:41:10,商户消费,luckin coffee,"订单付款",支出,¥93.40,零钱,已退款(￥9.10),4200001879202307111251305441	,10113350741140217857	,"/"'
    line_data = test_data.split(",")
    assert wechat_loader._parse_cost(line_data) == 93.4
    assert wechat_loader._parse_type(line_data) == TransactionType.Expense
    type_ = wechat_loader._parse_type(line_data)
    assert wechat_loader._parse_account_from(line_data, type_) == "微信"
    assert wechat_loader._parse_classify(line_data, type_) == "咖啡"

    assert wechat_loader._parse_line(test_data)._cost == 84.3


def test_wechat_refund2(wechat_loader: WeChatBillLoader) -> None:
    test_data = '2023-07-11 14:41:10,商户消费,luckin coffee,"订单付款",收入,¥9.10,零钱,已退款(￥9.10),4200001879202307111251305441	,10113350741140217857	,"/"'
    assert wechat_loader._parse_line(test_data) is None

    test_data = '2023-04-28 10:32:35,转账,xxx,"转账备注:微信转账",支出,¥180.00,零钱,对方已退还,100005000123042800081247616705202984	,1000050001202304280219702510896	,"/"'
    assert wechat_loader._parse_line(test_data) is None

    test_data = '2023-04-28 10:34:29,转账-退款,/,"转账备注:微信转账",收入,¥180.00,零钱,已全额退款,1000050001202304280219702510896	,	,"/"'
    assert wechat_loader._parse_line(test_data) is None

    test_data = '2023-01-15 12:53:58,南越王博物院（西汉南越国史研究中心）-退款,南越王博物院（西汉南越国史研究中心）,"南越王博物院（西汉南越国史研究中心）",收入,¥20.00,招商银行(0638),已全额退款,50302304522023011529958682250	,	,"/"'
    assert wechat_loader._parse_line(test_data) is None

    test_data = '2023-01-15 11:02:49,商户消费,南越王博物院（西汉南越国史研究中心）,"10836317|普通票|单个",支出,¥20.00,招商银行(0638),已全额退款,4200001653202301150174201960	,10490823	,"/"'
    assert wechat_loader._parse_line(test_data) is None


def test_wechat_transfer(wechat_loader: WeChatBillLoader) -> None:
    test_data = '2023-04-06 12:20:44,零钱提现,招商银行(2508),"/",/,¥242.72,招商银行(2508),提现已到账,207230406100381248159221389	,/	,"服务费¥0.24"'
    data = wechat_loader._parse_line(test_data)

    assert data.dump() == "2023/04/06 12:20:44,,转账,242.72,微信,招行工资卡(0702),wechat--招商银行(2508)--/--[TID:207230406100381248159221389],,"
