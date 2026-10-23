"""
古茗数仓模拟数据生成脚本

按固定随机种子生成 2025 年第一季度的门店饮品零售数据，写入 dw 库
维表数据量小，事实表数据量大，统一在一个脚本里生成，保证订单和明细的口径一致

用法：
    uv run python -m app.scripts.seed_guming_dw
"""

import asyncio
import random
from datetime import date, datetime, timedelta

import asyncmy

from app.conf.app_config import app_config

# 固定种子，保证每次重建得到同一份数据，便于复现实验结果
SEED = 20250101
START_DATE = date(2025, 1, 1)
END_DATE = date(2025, 3, 31)

REGIONS = [
    ("R001", "上海市", "上海", "一线", "华东"),
    ("R002", "浙江省", "杭州", "新一线", "华东"),
    ("R003", "浙江省", "宁波", "二线", "华东"),
    ("R004", "浙江省", "温州", "二线", "华东"),
    ("R005", "浙江省", "台州", "三线", "华东"),
    ("R006", "江苏省", "苏州", "新一线", "华东"),
    ("R007", "江苏省", "南京", "新一线", "华东"),
    ("R008", "安徽省", "合肥", "二线", "华东"),
    ("R009", "广东省", "广州", "一线", "华南"),
    ("R010", "广东省", "深圳", "一线", "华南"),
    ("R011", "广东省", "东莞", "新一线", "华南"),
    ("R012", "广东省", "佛山", "二线", "华南"),
    ("R013", "福建省", "福州", "二线", "华南"),
    ("R014", "福建省", "厦门", "二线", "华南"),
    ("R015", "福建省", "泉州", "二线", "华南"),
    ("R016", "广西壮族自治区", "南宁", "二线", "华南"),
    ("R017", "湖北省", "武汉", "新一线", "华中"),
    ("R018", "湖南省", "长沙", "新一线", "华中"),
    ("R019", "江西省", "南昌", "二线", "华中"),
    ("R020", "河南省", "郑州", "新一线", "华中"),
    ("R021", "四川省", "成都", "新一线", "西南"),
    ("R022", "重庆市", "重庆", "一线", "西南"),
    ("R023", "云南省", "昆明", "二线", "西南"),
    ("R024", "贵州省", "贵阳", "二线", "西南"),
    ("R025", "北京市", "北京", "一线", "华北"),
    ("R026", "天津市", "天津", "二线", "华北"),
    ("R027", "山东省", "济南", "二线", "华北"),
    ("R028", "河北省", "石家庄", "二线", "华北"),
]

# 城市 -> 门店数量。古茗门店集中在华东、华南，其他区域少量布点
STORE_PLAN = {
    "杭州": 5,
    "上海": 4,
    "宁波": 3,
    "温州": 2,
    "台州": 3,
    "苏州": 2,
    "南京": 2,
    "合肥": 1,
    "广州": 3,
    "深圳": 3,
    "东莞": 2,
    "佛山": 2,
    "福州": 2,
    "厦门": 1,
    "泉州": 1,
    "武汉": 2,
    "长沙": 2,
    "南昌": 1,
    "郑州": 1,
    "成都": 2,
    "重庆": 1,
    "昆明": 1,
    "北京": 2,
    "天津": 1,
    "济南": 1,
}

AREAS = {
    "杭州": ["西湖银泰", "滨江宝龙", "武林广场", "钱江新城", "城西银泰"],
    "上海": ["静安久光", "人民广场", "徐家汇", "五角场"],
    "宁波": ["天一广场", "鄞州万达", "东部银泰"],
    "温州": ["五马街", "瓯海万象城"],
    "台州": ["椒江万达", "黄岩吾悦", "温岭银泰"],
    "苏州": ["观前街", "园区久光"],
    "南京": ["新街口", "江宁万达"],
    "合肥": ["之心城"],
    "广州": ["天河城", "北京路", "番禺万博"],
    "深圳": ["海岸城", "华强北", "龙岗万科"],
    "东莞": ["南城鸿福路", "松山湖"],
    "佛山": ["祖庙", "南海万达"],
    "福州": ["东街口", "仓山万达"],
    "厦门": ["中山路"],
    "泉州": ["丰泽浦西"],
    "武汉": ["江汉路", "光谷世界城"],
    "长沙": ["五一广场", "梅溪湖"],
    "南昌": ["八一广场"],
    "郑州": ["二七广场"],
    "成都": ["春熙路", "太古里"],
    "重庆": ["解放碑"],
    "昆明": ["南屏街"],
    "北京": ["三里屯", "西单"],
    "天津": ["滨江道"],
    "济南": ["泉城路"],
}

# (product_id, 名称, 品类, 系列, 杯型, 售价, 成本, 上市日期, 状态, 热度权重)
PRODUCTS = [
    ("P001", "超A芝士葡萄", "鲜果茶", "经典系列", "大杯", 19.00, 7.20, "2024-06-01", "在售", 5),
    ("P002", "杨枝甘露", "鲜果茶", "经典系列", "大杯", 17.00, 6.10, "2023-05-01", "在售", 5),
    ("P003", "云岭茉莉白", "轻乳茶", "轻乳茶系列", "大杯", 16.00, 5.40, "2024-03-01", "在售", 4),
    ("P004", "龙井青团", "轻乳茶", "春季限定", "中杯", 18.00, 6.00, "2025-02-15", "在售", 3),
    ("P005", "生椰拿铁", "咖啡", "咖啡系列", "大杯", 17.00, 5.80, "2023-09-01", "在售", 3),
    ("P006", "芋泥波波奶茶", "奶茶", "经典系列", "大杯", 16.00, 5.60, "2022-10-01", "在售", 4),
    ("P007", "布蕾脆脆奶芙", "奶茶", "经典系列", "大杯", 17.00, 5.90, "2024-01-01", "在售", 3),
    ("P008", "青提茉莉", "鲜果茶", "季节限定", "大杯", 18.00, 6.20, "2024-07-01", "在售", 3),
    ("P009", "芝士莓莓", "鲜果茶", "季节限定", "大杯", 19.00, 6.70, "2024-12-01", "在售", 4),
    ("P010", "茉莉奶绿", "奶茶", "经典系列", "中杯", 13.00, 4.40, "2021-05-01", "在售", 3),
    ("P011", "黑糖珍珠奶茶", "奶茶", "经典系列", "大杯", 15.00, 5.00, "2021-03-01", "在售", 3),
    ("P012", "满杯红柚", "鲜果茶", "经典系列", "大杯", 17.00, 6.10, "2023-03-01", "在售", 2),
    ("P013", "芒果西米露", "鲜果茶", "季节限定", "大杯", 16.00, 5.50, "2024-05-01", "在售", 2),
    ("P014", "牛油果酸奶", "鲜果茶", "轻负担系列", "大杯", 20.00, 7.60, "2024-09-01", "在售", 2),
    ("P015", "抹茶拿铁", "咖啡", "咖啡系列", "中杯", 16.00, 5.70, "2023-11-01", "在售", 2),
    ("P016", "可可芭蕾", "奶茶", "经典系列", "大杯", 17.00, 6.00, "2022-12-01", "在售", 2),
    ("P017", "香水柠檬茶", "纯茶", "纯茶系列", "大杯", 12.00, 3.60, "2023-07-01", "在售", 3),
    ("P018", "四季春", "纯茶", "纯茶系列", "中杯", 10.00, 2.80, "2021-04-01", "在售", 2),
    ("P019", "冰淇淋红茶", "纯茶", "经典系列", "中杯", 11.00, 3.30, "2023-04-01", "在售", 2),
    ("P020", "芝士乌龙", "奶茶", "经典系列", "大杯", 16.00, 5.60, "2022-06-01", "在售", 2),
    ("P021", "桂花酒酿奶茶", "奶茶", "季节限定", "中杯", 16.00, 5.80, "2024-10-01", "下架", 1),
    ("P022", "草莓啵啵", "鲜果茶", "季节限定", "大杯", 18.00, 6.30, "2025-01-10", "在售", 4),
    ("P023", "芭乐柠檬茶", "鲜果茶", "季节限定", "大杯", 15.00, 5.10, "2025-02-01", "在售", 3),
    ("P024", "龙井奶绿", "轻乳茶", "春季限定", "大杯", 17.00, 5.70, "2025-03-01", "在售", 3),
    ("P025", "生椰抹茶", "咖啡", "咖啡系列", "大杯", 18.00, 6.40, "2024-08-01", "在售", 2),
    ("P026", "酒酿小圆子", "奶茶", "季节限定", "中杯", 15.00, 5.20, "2024-11-01", "下架", 1),
    ("P027", "轻乳茶·观音", "轻乳茶", "轻乳茶系列", "大杯", 16.00, 5.40, "2024-04-01", "在售", 3),
    ("P028", "黑桑莓莓", "鲜果茶", "季节限定", "大杯", 19.00, 6.60, "2024-12-15", "下架", 1),
    ("P029", "椰椰芒芒", "鲜果茶", "经典系列", "大杯", 18.00, 6.30, "2023-06-01", "在售", 3),
    ("P030", "多多柠檬茶", "鲜果茶", "经典系列", "大杯", 14.00, 4.70, "2023-02-01", "在售", 2),
    ("P031", "布蕾奶茶", "奶茶", "经典系列", "中杯", 14.00, 4.80, "2022-08-01", "在售", 2),
    ("P032", "芋圆牛乳", "奶茶", "经典系列", "中杯", 15.00, 5.30, "2023-01-01", "在售", 2),
    ("P033", "茉莉柠檬茶", "鲜果茶", "经典系列", "大杯", 14.00, 4.60, "2024-02-01", "在售", 2),
    ("P034", "青柑普洱", "纯茶", "纯茶系列", "中杯", 12.00, 3.40, "2024-03-01", "在售", 2),
    ("P035", "杨梅冰茶", "鲜果茶", "季节限定", "大杯", 17.00, 5.90, "2024-06-15", "下架", 1),
    ("P036", "桂花乌龙", "纯茶", "纯茶系列", "中杯", 11.00, 3.20, "2023-09-01", "在售", 1),
    ("P037", "燕麦拿铁", "咖啡", "咖啡系列", "中杯", 18.00, 6.30, "2024-01-15", "在售", 2),
    ("P038", "厚芋泥奶茶", "奶茶", "经典系列", "大杯", 17.00, 5.80, "2022-11-01", "在售", 2),
    ("P039", "葡萄冻冻", "鲜果茶", "经典系列", "大杯", 17.00, 5.90, "2023-08-01", "在售", 2),
    ("P040", "桃桃乌龙", "鲜果茶", "季节限定", "大杯", 16.00, 5.40, "2025-03-10", "在售", 3),
]

# 古茗对外常用的产品线/家族命名，避免出现“经典系列”这类通用说法
SERIES_BY_PRODUCT = {
    "P001": "超A芝士家族",
    "P002": "鲜果茶家族",
    "P003": "云岭茉莉家族",
    "P004": "轻乳茶家族",
    "P005": "咖啡家族",
    "P006": "经典奶茶家族",
    "P007": "经典奶茶家族",
    "P008": "鲜果茶家族",
    "P009": "超A芝士家族",
    "P010": "经典奶茶家族",
    "P011": "经典奶茶家族",
    "P012": "鲜果茶家族",
    "P013": "鲜果茶家族",
    "P014": "轻负担系列",
    "P015": "咖啡家族",
    "P016": "经典奶茶家族",
    "P017": "纯茶家族",
    "P018": "纯茶家族",
    "P019": "纯茶家族",
    "P020": "超A芝士家族",
    "P021": "季节限定",
    "P022": "季节限定",
    "P023": "季节限定",
    "P024": "轻乳茶家族",
    "P025": "咖啡家族",
    "P026": "季节限定",
    "P027": "轻乳茶家族",
    "P028": "季节限定",
    "P029": "鲜果茶家族",
    "P030": "鲜果茶家族",
    "P031": "经典奶茶家族",
    "P032": "经典奶茶家族",
    "P033": "鲜果茶家族",
    "P034": "纯茶家族",
    "P035": "季节限定",
    "P036": "纯茶家族",
    "P037": "咖啡家族",
    "P038": "经典奶茶家族",
    "P039": "鲜果茶家族",
    "P040": "季节限定",
}

CHANNELS = [
    ("CH01", "到店自提", "到店", "古茗小程序", 45),
    ("CH02", "小程序外卖", "外卖", "古茗小程序", 25),
    ("CH03", "美团外卖", "外卖", "美团", 20),
    ("CH04", "饿了么外卖", "外卖", "饿了么", 10),
]

# (activity_id, 名称, 类型, 开始, 结束, 折扣率, 门槛, 减免)
PROMOTIONS = [
    ("PR001", "周三会员日", "折扣", "2025-01-08", "2025-01-08", 0.80, None, None),
    ("PR002", "新春满30减5", "满减", "2025-01-20", "2025-02-05", None, 30.00, 5.00),
    ("PR003", "第二杯半价", "第二杯半价", "2025-01-01", "2025-03-31", 0.50, None, None),
    ("PR004", "情人节买一送一", "买一送一", "2025-02-14", "2025-02-14", None, None, None),
    ("PR005", "周末满20减3", "满减", "2025-01-04", "2025-03-30", None, 20.00, 3.00),
    ("PR006", "9.9元喝新品", "折扣", "2025-02-15", "2025-03-15", 0.55, None, None),
    ("PR007", "女神节第二杯半价", "第二杯半价", "2025-03-08", "2025-03-08", 0.50, None, None),
    ("PR008", "葫芦兑好礼", "赠品", "2025-01-01", "2025-03-31", None, None, None),
    ("PR009", "春日第二杯半价", "第二杯半价", "2025-03-01", "2025-03-31", 0.50, None, None),
    ("PR010", "新店开业满15减2", "满减", "2025-01-01", "2025-01-15", None, 15.00, 2.00),
]

SURNAMES = list("王李张刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾肖田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤")
GIVEN_CHARS = list("伟芳娜敏静丽强磊军洋勇艳杰娟涛明超秀霞平刚桂英华萍玲燕红鹏辉建文玉兰凤云彬宇浩凯鑫欣怡婷雪梅琳晨阳佳慧嘉宁思远子涵梓萱雨桐一诺")

GENDERS = ["女", "男", "未知"]
GENDER_WEIGHTS = [52, 45, 3]
AGE_GROUPS = ["18岁以下", "18-24", "25-30", "31-40", "40岁以上"]
AGE_WEIGHTS = [3, 30, 35, 22, 10]
# 古茗茗星会员四级：潜力 <3 葫芦、人气 >=3、当红 >=8、顶流 >=20（每月 1 日按上月葫芦结算）
MEMBER_LEVELS = ["潜力茗星", "人气茗星", "当红茗星", "顶流茗星"]
LEVEL_WEIGHTS = [60, 25, 12, 3]

TOPPINGS = ["无", "珍珠", "椰果", "多肉", "芋圆", "芋泥", "奶盖", "西米"]
TOPPING_WEIGHTS = [55, 12, 8, 8, 6, 5, 4, 2]
TOPPING_PRICES = {
    "无": 0.0,
    "珍珠": 1.0,
    "椰果": 1.0,
    "多肉": 1.0,
    "芋圆": 2.0,
    "芋泥": 3.0,
    "奶盖": 3.0,
    "西米": 1.0,
}
# 古茗点单口径：七分甜是默认甜度，微糖即不另外加糖
SUGAR_LEVELS = ["十分甜", "七分甜", "五分甜", "三分甜", "微糖"]
SUGAR_WEIGHTS = [15, 40, 25, 15, 5]
ICE_LEVELS = ["正常冰", "少冰", "去冰", "温", "热"]
ICE_WEIGHTS = [40, 25, 10, 15, 10]
ORDER_HOURS = list(range(9, 23))
ORDER_HOUR_WEIGHTS = [2, 3, 4, 3, 5, 6, 6, 5, 7, 8, 8, 6, 4, 2]
WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def build_stores(rng: random.Random):
    """按城市分布生成 50 家门店，并给每家门店一个热度系数"""
    city_region = {city: region_id for region_id, _, city, _, _ in REGIONS}
    stores = []
    index = 1
    for city, count in STORE_PLAN.items():
        for area in AREAS[city][:count]:
            store_id = f"S{index:03d}"
            store_type = "直营店" if index % 25 == 1 else "加盟店"
            open_date = date(2021, 1, 1) + timedelta(days=rng.randint(0, 1460))
            area_sqm = round(rng.uniform(28, 95), 1)
            # 热度系数决定每天的单量，让“头部门店”这类问题有真实分布
            popularity = rng.uniform(0.7, 1.6)
            stores.append(
                (
                    store_id,
                    f"古茗({city}{area}店)",
                    city_region[city],
                    store_type,
                    open_date,
                    "营业",
                    area_sqm,
                    popularity,
                )
            )
            index += 1

    # 末尾三家门店分别设为闭店和筹备，问数时需要先筛 status
    for position, status in ((-3, "闭店"), (-2, "闭店"), (-1, "筹备")):
        store = list(stores[position])
        store[5] = status
        stores[position] = tuple(store)

    return stores


def build_products():
    """把商品配置整理成后续生成订单时使用的元组"""
    products = []
    for (
        product_id,
        name,
        category,
        series,
        cup_size,
        list_price,
        cost_price,
        launch_date,
        status,
        weight,
    ) in PRODUCTS:
        products.append(
            {
                "product_id": product_id,
                "product_name": name,
                "category": category,
                "series": SERIES_BY_PRODUCT.get(product_id, series),
                "cup_size": cup_size,
                "list_price": list_price,
                "cost_price": cost_price,
                "launch_date": date.fromisoformat(launch_date),
                "status": status,
                "weight": weight,
            }
        )
    return products


def build_dates():
    """展开 2025-01-01 到 2025-03-31 的日期维度"""
    dates = []
    current = START_DATE
    while current <= END_DATE:
        dates.append(
            (
                int(current.strftime("%Y%m%d")),
                current,
                current.year,
                f"Q{(current.month - 1) // 3 + 1}",
                current.month,
                current.day,
                current.isoweekday(),
                WEEKDAY_NAMES[current.isoweekday() - 1],
                1 if current.isoweekday() >= 6 else 0,
            )
        )
        current += timedelta(days=1)
    return dates


def build_members(rng: random.Random, stores):
    """生成 3000 位会员，注册门店只落在营业中的门店上"""
    open_store_ids = [store[0] for store in stores if store[5] == "营业"]
    members = []
    for index in range(1, 3001):
        member_name = rng.choice(SURNAMES) + "".join(
            rng.choice(GIVEN_CHARS) for _ in range(rng.choice([1, 2]))
        )
        register_date = date(2023, 1, 1) + timedelta(days=rng.randint(0, 819))
        members.append(
            (
                f"M{index:05d}",
                member_name,
                rng.choices(GENDERS, weights=GENDER_WEIGHTS, k=1)[0],
                rng.choices(AGE_GROUPS, weights=AGE_WEIGHTS, k=1)[0],
                rng.choices(MEMBER_LEVELS, weights=LEVEL_WEIGHTS, k=1)[0],
                register_date,
                rng.choice(open_store_ids),
            )
        )

    # 按注册日期排序，下单时只从“当天已经注册”的会员里选，避免出现未来会员
    members.sort(key=lambda item: item[5])
    return members


def build_promotions():
    promotions = []
    for (
        promotion_id,
        name,
        promotion_type,
        start_date,
        end_date,
        discount_rate,
        threshold_amount,
        reduce_amount,
    ) in PROMOTIONS:
        promotions.append(
            {
                "promotion_id": promotion_id,
                "promotion_name": name,
                "promotion_type": promotion_type,
                "start_date": date.fromisoformat(start_date),
                "end_date": date.fromisoformat(end_date),
                "discount_rate": discount_rate,
                "threshold_amount": threshold_amount,
                "reduce_amount": reduce_amount,
            }
        )
    return promotions


def calculate_discount(promotion, order_amount, unit_prices, total_quantity):
    """按活动类型计算优惠金额；不满足门槛时返回 0"""
    if promotion is None:
        return 0.0

    promotion_type = promotion["promotion_type"]
    if promotion_type == "折扣":
        return round(order_amount * (1 - promotion["discount_rate"]), 2)
    if promotion_type == "满减":
        if order_amount >= promotion["threshold_amount"]:
            return promotion["reduce_amount"]
        return 0.0
    if promotion_type == "第二杯半价":
        if total_quantity >= 2:
            return round(min(unit_prices) * 0.5, 2)
        return 0.0
    if promotion_type == "买一送一":
        if total_quantity >= 2:
            return round(min(unit_prices), 2)
        return 0.0
    # 赠品活动不改变订单金额，这里视为没有优惠
    return 0.0


def build_facts(rng: random.Random, stores, products, members, dates, promotions):
    """生成订单与订单明细，两个列表的下标口径完全一致"""
    open_stores = [store for store in stores if store[5] == "营业"]
    member_dates = [member[5] for member in members]
    member_pointer = 0

    order_rows = []
    item_rows = []
    order_seq = 0

    for date_id, current_date, *_ in dates:
        # 推进会员可下单范围
        while member_pointer < len(members) and member_dates[member_pointer] <= current_date:
            member_pointer += 1

        # 当天在售且已经上市的商品
        day_products = [
            product
            for product in products
            if product["status"] == "在售" and product["launch_date"] <= current_date
        ]
        day_product_weights = [product["weight"] for product in day_products]

        # 当天生效的活动
        day_promotions = [
            promotion
            for promotion in promotions
            if promotion["start_date"] <= current_date <= promotion["end_date"]
        ]

        for store in open_stores:
            store_id = store[0]
            popularity = store[7]
            order_count = max(3, int(rng.uniform(8, 14) * popularity))

            for _ in range(order_count):
                order_seq += 1
                order_id = f"GM{date_id}{order_seq:06d}"

                line_count = rng.choices([1, 2, 3], weights=[62, 30, 8], k=1)[0]
                chosen_products = rng.choices(
                    day_products, weights=day_product_weights, k=line_count
                )

                lines = []
                order_amount = 0.0
                total_quantity = 0
                unit_prices = []

                for line_no, product in enumerate(chosen_products, start=1):
                    quantity = rng.choices([1, 2, 3], weights=[82, 15, 3], k=1)[0]
                    topping = rng.choices(
                        TOPPINGS, weights=TOPPING_WEIGHTS, k=1
                    )[0]
                    topping_amount = round(TOPPING_PRICES[topping] * quantity, 2)
                    item_amount = round(
                        product["list_price"] * quantity + topping_amount, 2
                    )

                    lines.append(
                        (
                            f"OI{order_seq:07d}{line_no:02d}",
                            order_id,
                            product["product_id"],
                            quantity,
                            product["list_price"],
                            item_amount,
                            rng.choices(
                                SUGAR_LEVELS, weights=SUGAR_WEIGHTS, k=1
                            )[0],
                            rng.choices(ICE_LEVELS, weights=ICE_WEIGHTS, k=1)[0],
                            topping,
                            topping_amount,
                        )
                    )
                    order_amount += item_amount
                    total_quantity += quantity
                    unit_prices.append(product["list_price"])

                order_amount = round(order_amount, 2)

                # 30% 的订单参与活动；算不出优惠就不挂活动
                promotion = None
                discount_amount = 0.0
                if day_promotions and rng.random() < 0.30:
                    candidate = rng.choice(day_promotions)
                    candidate_discount = calculate_discount(
                        candidate, order_amount, unit_prices, total_quantity
                    )
                    if candidate_discount > 0:
                        promotion = candidate
                        discount_amount = round(min(candidate_discount, order_amount), 2)

                status_roll = rng.random()
                if status_roll < 0.03:
                    order_status = "已退款"
                elif status_roll < 0.06:
                    order_status = "已取消"
                else:
                    order_status = "已完成"

                # 退款和取消的订单不计入实收；保留原价和优惠，方便演示口径过滤
                if order_status == "已完成":
                    actual_amount = round(order_amount - discount_amount, 2)
                else:
                    actual_amount = 0.0

                member_id = None
                if member_pointer > 0 and rng.random() < 0.65:
                    member_id = members[rng.randrange(member_pointer)][0]

                channel = rng.choices(
                    CHANNELS, weights=[channel[4] for channel in CHANNELS], k=1
                )[0]

                hour = rng.choices(ORDER_HOURS, weights=ORDER_HOUR_WEIGHTS, k=1)[0]
                order_time = datetime(
                    current_date.year,
                    current_date.month,
                    current_date.day,
                    hour,
                    rng.randint(0, 59),
                    rng.randint(0, 59),
                )

                order_rows.append(
                    (
                        order_id,
                        store_id,
                        member_id,
                        date_id,
                        channel[0],
                        promotion["promotion_id"] if promotion else None,
                        order_amount,
                        discount_amount,
                        actual_amount,
                        total_quantity,
                        order_status,
                        order_time,
                    )
                )
                item_rows.extend(lines)

    return order_rows, item_rows


async def insert_in_batches(cursor, sql: str, rows: list[tuple], batch_size=5000):
    for start in range(0, len(rows), batch_size):
        await cursor.executemany(sql, rows[start : start + batch_size])


async def seed():
    rng = random.Random(SEED)

    stores = build_stores(rng)
    products = build_products()
    dates = build_dates()
    members = build_members(rng, stores)
    promotions = build_promotions()
    order_rows, item_rows = build_facts(
        rng, stores, products, members, dates, promotions
    )

    db = app_config.db_dw
    conn = await asyncmy.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        password=db.password,
        db=db.database,
        charset="utf8mb4",
        autocommit=False,
    )
    try:
        async with conn.cursor() as cursor:
            for table in (
                "fact_order_item",
                "fact_order",
                "dim_member",
                "dim_date",
                "dim_promotion",
                "dim_channel",
                "dim_product",
                "dim_store",
                "dim_region",
            ):
                await cursor.execute(f"TRUNCATE TABLE {table}")

            await cursor.executemany(
                "INSERT INTO dim_region (region_id, province, city, city_level, region_name) VALUES (%s, %s, %s, %s, %s)",
                REGIONS,
            )
            await cursor.executemany(
                "INSERT INTO dim_store (store_id, store_name, region_id, store_type, open_date, status, area_sqm) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                [(store[0], store[1], store[2], store[3], store[4], store[5], store[6]) for store in stores],
            )
            await cursor.executemany(
                "INSERT INTO dim_product (product_id, product_name, category, series, cup_size, list_price, cost_price, launch_date, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                [
                    (
                        product["product_id"],
                        product["product_name"],
                        product["category"],
                        product["series"],
                        product["cup_size"],
                        product["list_price"],
                        product["cost_price"],
                        product["launch_date"],
                        product["status"],
                    )
                    for product in products
                ],
            )
            await cursor.executemany(
                "INSERT INTO dim_channel (channel_id, channel_name, channel_type, platform) VALUES (%s, %s, %s, %s)",
                [(channel[0], channel[1], channel[2], channel[3]) for channel in CHANNELS],
            )
            await cursor.executemany(
                "INSERT INTO dim_promotion (promotion_id, promotion_name, promotion_type, start_date, end_date, discount_rate, threshold_amount, reduce_amount) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                [
                    (
                        promotion["promotion_id"],
                        promotion["promotion_name"],
                        promotion["promotion_type"],
                        promotion["start_date"],
                        promotion["end_date"],
                        promotion["discount_rate"],
                        promotion["threshold_amount"],
                        promotion["reduce_amount"],
                    )
                    for promotion in promotions
                ],
            )
            await cursor.executemany(
                "INSERT INTO dim_date (date_id, date, year, quarter, month, day, weekday, weekday_name, is_weekend) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                dates,
            )
            await cursor.executemany(
                "INSERT INTO dim_member (member_id, member_name, gender, age_group, member_level, register_date, register_store_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                members,
            )

            await insert_in_batches(
                cursor,
                "INSERT INTO fact_order (order_id, store_id, member_id, date_id, channel_id, promotion_id, order_amount, discount_amount, actual_amount, item_count, order_status, order_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                order_rows,
            )
            await insert_in_batches(
                cursor,
                "INSERT INTO fact_order_item (order_item_id, order_id, product_id, quantity, unit_price, item_amount, sugar_level, ice_level, topping, topping_amount) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                item_rows,
            )

        await conn.commit()
        print(
            f"古茗数仓造数完成：门店 {len(stores)}，商品 {len(products)}，会员 {len(members)}，"
            f"日期 {len(dates)}，订单 {len(order_rows)}，订单明细 {len(item_rows)}"
        )
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(seed())
