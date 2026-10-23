SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS dw DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
GRANT ALL PRIVILEGES ON dw.* TO 'goblin'@'%';
USE dw;

-- 古茗门店饮品零售数仓
-- 粒度：订单事实表一行一个订单，订单明细表一行一个饮品 SKU
-- 维表与事实表数据由 app/scripts/seed_guming_dw.py 生成

DROP TABLE IF EXISTS fact_order_item;
DROP TABLE IF EXISTS fact_order;
DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_promotion;
DROP TABLE IF EXISTS dim_channel;
DROP TABLE IF EXISTS dim_member;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_store;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_region;


CREATE TABLE dim_region
(
    region_id   VARCHAR(20) PRIMARY KEY COMMENT '区域编号',
    province    VARCHAR(50) COMMENT '省份',
    city        VARCHAR(50) COMMENT '城市',
    city_level  VARCHAR(20) COMMENT '城市等级(一线/新一线/二线/三线)',
    region_name VARCHAR(50) COMMENT '大区'
) COMMENT '地区维度表：城市粒度，用于门店归属和大区分析';


CREATE TABLE dim_store
(
    store_id   VARCHAR(20) PRIMARY KEY COMMENT '门店编号',
    store_name VARCHAR(100) COMMENT '门店名称',
    region_id  VARCHAR(20) COMMENT '所属区域编号',
    store_type VARCHAR(20) COMMENT '门店类型(直营/加盟)',
    open_date  DATE COMMENT '开业日期',
    status     VARCHAR(20) COMMENT '门店状态(营业/闭店/筹备)',
    area_sqm   DECIMAL(8, 2) COMMENT '门店营业面积(平方米)'
) COMMENT '门店维度表：一行一家古茗门店';


CREATE TABLE dim_product
(
    product_id   VARCHAR(20) PRIMARY KEY COMMENT '商品编号',
    product_name VARCHAR(100) COMMENT '饮品名称',
    category     VARCHAR(30) COMMENT '饮品品类',
    series       VARCHAR(30) COMMENT '产品系列',
    cup_size     VARCHAR(10) COMMENT '杯型(中杯/大杯)',
    list_price   DECIMAL(8, 2) COMMENT '标准售价(元/杯)',
    cost_price   DECIMAL(8, 2) COMMENT '单位成本(元/杯)',
    launch_date  DATE COMMENT '上市日期',
    status       VARCHAR(20) COMMENT '商品状态(在售/下架)'
) COMMENT '商品维度表：一行一个饮品 SKU';


CREATE TABLE dim_member
(
    member_id         VARCHAR(20) PRIMARY KEY COMMENT '会员编号',
    member_name       VARCHAR(50) COMMENT '会员姓名',
    gender            VARCHAR(10) COMMENT '性别',
    age_group         VARCHAR(20) COMMENT '年龄段',
    member_level      VARCHAR(20) COMMENT '会员等级',
    register_date     DATE COMMENT '注册日期',
    register_store_id VARCHAR(20) COMMENT '注册门店编号'
) COMMENT '会员维度表：一行一位注册会员';


CREATE TABLE dim_channel
(
    channel_id   VARCHAR(20) PRIMARY KEY COMMENT '渠道编号',
    channel_name VARCHAR(50) COMMENT '渠道名称',
    channel_type VARCHAR(20) COMMENT '渠道类型(到店/外卖)',
    platform     VARCHAR(50) COMMENT '所属平台'
) COMMENT '渠道维度表：门店自提与各类外卖渠道';


CREATE TABLE dim_promotion
(
    promotion_id     VARCHAR(20) PRIMARY KEY COMMENT '活动编号',
    promotion_name   VARCHAR(100) COMMENT '活动名称',
    promotion_type   VARCHAR(30) COMMENT '活动类型(折扣/满减/第二杯半价/赠品)',
    start_date       DATE COMMENT '开始日期',
    end_date         DATE COMMENT '结束日期',
    discount_rate    DECIMAL(4, 2) COMMENT '折扣率(0.8 表示八折)',
    threshold_amount DECIMAL(8, 2) COMMENT '满减门槛金额(元)',
    reduce_amount    DECIMAL(8, 2) COMMENT '满减减免金额(元)'
) COMMENT '促销活动维度表：折扣、满减、第二杯半价等';


CREATE TABLE dim_date
(
    date_id      INT PRIMARY KEY COMMENT '日期编号 yyyyMMdd',
    date         DATE COMMENT '业务日期',
    year         INT COMMENT '年份',
    quarter      VARCHAR(2) COMMENT '季度',
    month        INT COMMENT '月份',
    day          INT COMMENT '日',
    weekday      INT COMMENT '星期几(1=周一)',
    weekday_name VARCHAR(10) COMMENT '星期名称',
    is_weekend   TINYINT COMMENT '是否周末(1是/0否)'
) COMMENT '日期维度表：2025 年第一季度按天展开';


CREATE TABLE fact_order
(
    order_id        VARCHAR(40) PRIMARY KEY COMMENT '订单编号',
    store_id        VARCHAR(20) COMMENT '门店编号',
    member_id       VARCHAR(20) COMMENT '会员编号(非会员下单为空)',
    date_id         INT COMMENT '下单日期编号',
    channel_id      VARCHAR(20) COMMENT '下单渠道编号',
    promotion_id    VARCHAR(20) COMMENT '使用的促销活动编号',
    order_amount    DECIMAL(10, 2) COMMENT '原价金额(元)',
    discount_amount DECIMAL(10, 2) COMMENT '优惠金额(元)',
    actual_amount   DECIMAL(10, 2) COMMENT '实收金额(元)',
    item_count      INT COMMENT '出杯数',
    order_status    VARCHAR(20) COMMENT '订单状态(已完成/已退款/已取消)',
    order_time      DATETIME COMMENT '下单时间',
    KEY idx_order_store (store_id),
    KEY idx_order_member (member_id),
    KEY idx_order_date (date_id),
    KEY idx_order_channel (channel_id)
) COMMENT '订单事实表：一行一个订单';


CREATE TABLE fact_order_item
(
    order_item_id  VARCHAR(40) PRIMARY KEY COMMENT '订单明细编号',
    order_id       VARCHAR(40) COMMENT '订单编号',
    product_id     VARCHAR(20) COMMENT '商品编号',
    quantity       INT COMMENT '购买杯数',
    unit_price     DECIMAL(8, 2) COMMENT '单杯售价(元)',
    item_amount    DECIMAL(10, 2) COMMENT '明细金额(元)',
    sugar_level    VARCHAR(20) COMMENT '糖度',
    ice_level      VARCHAR(20) COMMENT '冰量',
    topping        VARCHAR(20) COMMENT '小料',
    topping_amount DECIMAL(6, 2) COMMENT '小料金额(元)',
    KEY idx_item_order (order_id),
    KEY idx_item_product (product_id)
) COMMENT '订单明细事实表：一行一个饮品 SKU';
