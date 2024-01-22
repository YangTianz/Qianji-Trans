import pytest

from billing.bill_loader import AlipayBillLoader
from billing.const import TransactionType


@pytest.fixture(scope="module")
def alipay_loader(account_rules_list, classify_rules_list):
    return AlipayBillLoader(account_rules_list, classify_rules_list)


def test_alipay_expense(alipay_loader: AlipayBillLoader) -> None:
    test_data = '2023-12-08 20:19:03,交通出行,高德打车,aut***@autonavi.com,高德地图打车订单,支出,16.60,招商银行信用卡(0638),交易成功,2023120822001489491457440137	,0003N202312080000000004969205443	,,'
    line_data = test_data.split(",")
    assert alipay_loader._parse_cost(line_data) == 16.6
    assert alipay_loader._parse_type(line_data) == TransactionType.Expense
    type_ = alipay_loader._parse_type(line_data)
    assert alipay_loader._parse_account_from(line_data, type_) == "招行信用卡(0638)"
    assert alipay_loader._parse_classify(line_data, type_) == "打车"


def test_alipay_expense2(alipay_loader: AlipayBillLoader) -> None:
    test_data = '2023-10-05 19:04:08,日用百货,广州盒马,shh***@163.com,青岛啤酒 棕金11度 296ml等多件,支出,45.50,招商银行信用卡(0638),交易成功,2023100522001189491415233828	,T200P1984800036541368984	,,'
    line_data = test_data.split(",")
    assert alipay_loader._parse_cost(line_data) == 45.5
    assert alipay_loader._parse_type(line_data) == TransactionType.Expense
    type_ = alipay_loader._parse_type(line_data)
    assert alipay_loader._parse_account_from(line_data, type_) == "招行信用卡(0638)"
    assert alipay_loader._parse_classify(line_data, type_) == "买菜"


def test_alipay_income(alipay_loader: AlipayBillLoader) -> None:
    test_data = '2023-07-19 22:35:07,其他,Krung Thai Bank Public Company Limited,/,海外退税金,收入,23.79,,退税成功,2023071917038891	,10000011009	,,'
    line_data = test_data.split(",")
    assert alipay_loader._parse_cost(line_data) == 23.79
    assert alipay_loader._parse_type(line_data) == TransactionType.Income
    type_ = alipay_loader._parse_type(line_data)
    assert alipay_loader._parse_account_from(line_data, type_) == "支付宝"
    assert alipay_loader._parse_classify(line_data, type_) == ""


def test_alipay_refund(alipay_loader: AlipayBillLoader) -> None:
    test_data = """
    2023-06-20 12:56:34,日用百货,x***6,199******10,绿米Aqara M1S 2022款，2021款网关苹果Hom,支出,587.00,招商银行储蓄卡(2508),交易关闭,2023062022001189491456271034	,T200P1919215273591368984	,,
    2023-06-21 22:36:41,退款,x***6,199******10,退款-绿米Aqara M1S 2022款，2021款网关苹果Hom,不计收支,587.00,招商银行储蓄卡(2508),退款成功,2023062022001189491456271034_1919215273591368984	,T200P1919215273591368984	,,
    """
    assert len(alipay_loader.parse_file_content(test_data)) == 0

    test_data = '2023-07-26 17:56:00,交通出行,Greater Bay Airlines Co. Ltd,rsc***@worldpay.com,WPMUS713BV21-2023072602507827,不计收支,3234.00,,交易关闭,2023072622001389491458947363	,0007720035697034	,,'
    assert alipay_loader._parse_line(test_data) is None


def test_alipay_refund2(alipay_loader: AlipayBillLoader) -> None:
    test_data = """
    2023-12-11 10:00:23,交通出行,高德打车,aut***@autonavi.com,退款-高德地图打车订单,不计收支,38.75,招商银行信用卡(0638),退款成功,2023121122001489491410688387_20231211100023_3026554	,0001N202312110000000004996629381	,,
    2023-12-11 10:00:21,交通出行,高德打车,aut***@autonavi.com,高德地图打车订单,支出,38.75,招商银行信用卡(0638),交易关闭,2023121122001489491410688387	,0001N202312110000000004996629381	,,
    """
    assert len(alipay_loader.parse_file_content(test_data)) == 0


def test_alipay_refund3(alipay_loader: AlipayBillLoader) -> None:
    test_data = """
    2023-09-13 14:50:29,退款,蓝海**h,mpe***@163.com,退款-【sayl腰托配件】sayl人体工学椅腰托上下可调仅适用赫曼米勒sayl,不计收支,240.00,招商银行储蓄卡(2508),退款成功,2023090722001189491427922640_1966875997235368984_advance	,T200P1966875997235368984	,,
    2023-09-07 10:15:02,家居家装,蓝海**h,mpe***@163.com,【sayl腰托配件】sayl人体工学椅腰托上下可调仅适用赫曼米勒sayl,支出,240.00,招商银行储蓄卡(2508),交易关闭,2023090722001189491427922640	,T200P1966875997235368984	,,
    """
    assert len(alipay_loader.parse_file_content(test_data)) == 0


def test_alipay_refund4(alipay_loader: AlipayBillLoader) -> None:
    test_data = """
    2023-08-27 13:00:50,退款,豆浆**0,158******62,退款-汽车改色膜 全国包施工 远峰蓝魅金 远峰蓝魅绿 防撞保护膜全车膜,不计收支,2688.00,招商银行储蓄卡(2508),退款成功,2023082722001189491415108739_1958553660469368984	,T200P1958553660469368984	,,
    2023-08-27 13:00:45,爱车养车,豆浆**0,158******62,汽车改色膜 全国包施工 远峰蓝魅金 远峰蓝魅绿 防撞保护膜全车膜,支出,1188.00,招商银行储蓄卡(2508),交易成功,2023082722001189491414932348	,T200P1959320318938368984	,,
    2023-08-27 12:02:58,爱车养车,豆浆**0,158******62,汽车改色膜 全国包施工 远峰蓝魅金 远峰蓝魅绿 防撞保护膜全车膜,支出,2688.00,招商银行储蓄卡(2508),交易关闭,2023082722001189491415108739	,T200P1958553660469368984	,,
    """
    ret = alipay_loader.parse_file_content(test_data)
    assert len(ret) == 1
    data = ret[0]
    assert data._cost == 1188
    assert data._acc_from == "招行工资卡(0702)"
    assert data._type == TransactionType.Expense


def test_alipay_refund5(alipay_loader: AlipayBillLoader) -> None:
    test_data = """
    2023-06-28 14:42:11,退款,阿斯**店,liu***@powev.com,退款-【狂欢价】阿斯加特女武神8g16g32g ddr4 3200 3600台式机电脑内存条RGB灯条,不计收支,275.40,招商银行信用卡(0638),退款成功,2023062022001189491456142722_1919689285670368984_advance	,T200P1919689285670368984	,,
    2023-06-20 21:48:53,数码电器,阿斯**店,liu***@powev.com,【狂欢价】阿斯加特女武神8g16g32g ddr4 3200 3600台式机电脑内存条RGB灯条,支出,545.49,招商银行信用卡(0638),交易关闭,2023062022001189491456142722	,T200P1919689285670368984	,,
    """
    ret = alipay_loader.parse_file_content(test_data)
    assert len(ret) == 1
    data = ret[0]
    assert data._cost == 270.09
    assert data._acc_from == "招行信用卡(0638)"
    assert data._type == TransactionType.Expense


def test_alipay_refund6(alipay_loader: AlipayBillLoader) -> None:
    test_data = """
    2023-06-16 23:25:19,退款,天**,tmc***@service.aliyun.com,退款-洽洽小而香西瓜子奶油味540g大包装休闲零食袋中袋独立小包装恰恰 等多件,不计收支,37.90,招商银行信用卡(0638),退款成功,2023061622001189491445992902_1915372743014368984	,T200P1915372743013368984	,,
    2023-06-16 23:23:33,退款,天**,tmc***@service.aliyun.com,退款-洽洽小而香西瓜子奶油味540g大包装休闲零食袋中袋独立小包装恰恰 等多件,不计收支,40.66,招商银行信用卡(0638),退款成功,2023061622001189491445992902_1915372743016368984	,T200P1915372743013368984	,,
    2023-06-16 23:23:26,退款,天**,tmc***@service.aliyun.com,退款-洽洽小而香西瓜子奶油味540g大包装休闲零食袋中袋独立小包装恰恰 等多件,不计收支,30.25,招商银行信用卡(0638),退款成功,2023061622001189491445992902_1915372743017368984	,T200P1915372743013368984	,,
    2023-06-16 23:23:22,退款,天**,tmc***@service.aliyun.com,退款-洽洽小而香西瓜子奶油味540g大包装休闲零食袋中袋独立小包装恰恰 等多件,不计收支,28.41,招商银行信用卡(0638),退款成功,2023061622001189491445992902_1915372743015368984	,T200P1915372743013368984	,,
    2023-06-16 23:21:25,退款,天**,tmc***@service.aliyun.com,退款-洽洽小而香西瓜子奶油味540g大包装休闲零食袋中袋独立小包装恰恰 等多件,不计收支,21.66,招商银行信用卡(0638),退款成功,2023061622001189491445992902_1915372743018368984	,T200P1915372743013368984	,,
    2023-06-16 22:36:49,餐饮美食,天**,tmc***@service.aliyun.com,洽洽小而香西瓜子奶油味540g大包装休闲零食袋中袋独立小包装恰恰 等多件,支出,158.88,招商银行信用卡(0638),交易关闭,2023061622001189491445992902	,T200P1915372743013368984	,,
    """
    assert len(alipay_loader.parse_file_content(test_data)) == 0


def test_alipay_refund7(alipay_loader: AlipayBillLoader) -> None:
    test_data = """
    2023-04-17 20:09:07,退款,gr**店,gre***@cn.gree.com,退款-【来电价】【Gree/格力官方】一级变频3匹家用立式空调柜机冷暖两用客厅云颜 等多件,不计收支,3099.00,招商银行信用卡(0638),退款成功,2023041722001189491445339716_1870116096098368984	,T200P1870116096096368984	,,
    2023-04-17 20:09:03,退款,gr**店,gre***@cn.gree.com,退款-【来电价】【Gree/格力官方】一级变频3匹家用立式空调柜机冷暖两用客厅云颜 等多件,不计收支,7149.00,招商银行信用卡(0638),退款成功,2023041722001189491445339716_1870116096097368984	,T200P1870116096096368984	,,
    2023-04-17 20:02:34,数码电器,gr**店,gre***@cn.gree.com,【来电价】【Gree/格力官方】一级变频3匹家用立式空调柜机冷暖两用客厅云颜 等多件,支出,10198.00,招商银行信用卡(0638),交易成功,2023041722001189491447705819	,T200P1870858023983368984	,,
    2023-04-17 20:00:12,数码电器,gr**店,gre***@cn.gree.com,【来电价】【Gree/格力官方】一级变频3匹家用立式空调柜机冷暖两用客厅云颜 等多件,支出,10248.00,招商银行信用卡(0638),交易关闭,2023041722001189491445339716	,T200P1870116096096368984	,,
    """
    assert len(alipay_loader.parse_file_content(test_data)) == 1


def test_alipay_refund8(alipay_loader: AlipayBillLoader) -> None:
    test_data = """
    2023-03-24 12:14:39,退款,货拉拉,tjh***@huolala.cn,退款-货拉拉费用,不计收支,476.71,招商银行信用卡(0638),退款成功,2023032422001489491416584151_2010002399135844097916928	,1010002399094240075595776	,,
    2023-03-24 10:52:07,生活服务,货拉拉,tjh***@huolala.cn,货拉拉费用,支出,476.71,招商银行信用卡(0638),交易关闭,2023032422001489491416584151	,1010002399094240075595776	,,
    2023-03-24 10:46:46,退款,货拉拉,tjh***@huolala.cn,退款-货拉拉费用,不计收支,474.66,招商银行信用卡(0638),退款成功,2023032422001489491414886670_2010002399091606270779392	,1010002399089517381099520	,,
    2023-03-24 10:42:43,生活服务,货拉拉,tjh***@huolala.cn,货拉拉费用,支出,474.66,招商银行信用卡(0638),交易关闭,2023032422001489491414886670	,1010002399089517381099520	,,
    """
    assert len(alipay_loader.parse_file_content(test_data)) == 0


def test_alipay_refund9(alipay_loader: AlipayBillLoader) -> None:
    test_data = """
    2023-06-16 23:23:33,退款,天**,tmc***@service.aliyun.com,退款-洽洽小而香西瓜子奶油味540g大包装休闲零食袋中袋独立小包装恰恰 等多件,不计收支,40.66,招商银行信用卡(0638),退款成功,2023061622001189491445992902_1915372743016368984	,T200P1915372743013368984	,,
    2023-06-16 23:23:26,退款,天**,tmc***@service.aliyun.com,退款-洽洽小而香西瓜子奶油味540g大包装休闲零食袋中袋独立小包装恰恰 等多件,不计收支,30.25,招商银行信用卡(0638),退款成功,2023061622001189491445992902_1915372743017368984	,T200P1915372743013368984	,,
    2023-06-16 23:23:22,退款,天**,tmc***@service.aliyun.com,退款-洽洽小而香西瓜子奶油味540g大包装休闲零食袋中袋独立小包装恰恰 等多件,不计收支,28.41,招商银行信用卡(0638),退款成功,2023061622001189491445992902_1915372743015368984	,T200P1915372743013368984	,,
    2023-06-16 23:21:25,退款,天**,tmc***@service.aliyun.com,退款-洽洽小而香西瓜子奶油味540g大包装休闲零食袋中袋独立小包装恰恰 等多件,不计收支,21.66,招商银行信用卡(0638),退款成功,2023061622001189491445992902_1915372743018368984	,T200P1915372743013368984	,,
    2023-06-16 22:36:49,餐饮美食,天**,tmc***@service.aliyun.com,洽洽小而香西瓜子奶油味540g大包装休闲零食袋中袋独立小包装恰恰 等多件,支出,158.88,招商银行信用卡(0638),交易关闭,2023061622001189491445992902	,T200P1915372743013368984	,,
    """
    ret = alipay_loader.parse_file_content(test_data)
    # 37.9
    assert len(ret) == 1
    data = ret[0]
    assert data._cost == 37.9
    assert data._acc_from == "招行信用卡(0638)"
    assert data._type == TransactionType.Expense
