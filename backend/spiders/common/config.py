"""
电力交易中心数据源配置
记录各省级电力交易中心的公开数据URL、披露平台地址
注意：部分URL可能需要登录或在内网访问
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProvinceSource:
    """省份数据源配置"""
    province: str              # 省份名称
    short_code: str            # 简称，如 "粤", "鲁"
    exchange_name: str         # 电力交易中心名称
    website: str               # 官网
    disclosure_url: str        # 信息披露URL（可能有访问限制）
    api_hint: str              # API线索提示
    notes: str = ""            # 备注（访问限制说明）
    priority: int = 1          # 优先级 1-5，5最高


# 各省电力交易中心数据源（按优先级排序）
PROVINCE_SOURCES: dict[str, ProvinceSource] = {
    "广东": ProvinceSource(
        province="广东",
        short_code="粤",
        exchange_name="广东电力交易中心",
        website="https://www.gdep.com.cn",
        disclosure_url="https://www.gdep.com.cn/eprice/web/lists.html",
        api_hint="gdep.com.cn / 南方电网",
        notes="南方电网内网，可能无法直接访问",
        priority=5,
    ),
    "山东": ProvinceSource(
        province="山东",
        short_code="鲁",
        exchange_name="山东电力交易中心",
        website="https://www.sd.sgcc.com.cn",
        disclosure_url="https://www.sd.sgcc.com.cn/html/www/col/col8273/index.html",
        api_hint="国网山东 / sd.sgcc.com.cn",
        notes="国网内网，可能无法直接访问",
        priority=5,
    ),
    "江苏": ProvinceSource(
        province="江苏",
        short_code="苏",
        exchange_name="江苏电力交易中心",
        website="https://www.js.sgcc.com.cn",
        disclosure_url="https://www.js.sgcc.com.cn/html/www/col/col8276/index.html",
        api_hint="国网江苏 / js.sgcc.com.cn",
        notes="国网内网，可能无法直接访问",
        priority=4,
    ),
    "浙江": ProvinceSource(
        province="浙江",
        short_code="浙",
        exchange_name="浙江电力交易中心",
        website="https://www.zj.sgcc.com.cn",
        disclosure_url="https://www.zj.sgcc.com.cn/html/www/col/col8276/index.html",
        api_hint="国网浙江 / zj.sgcc.com.cn",
        notes="国网内网，可能无法直接访问",
        priority=4,
    ),
    "山西": ProvinceSource(
        province="山西",
        short_code="晋",
        exchange_name="山西电力交易中心",
        website="https://www.sx.sgcc.com.cn",
        disclosure_url="https://www.sx.sgcc.com.cn/html/www/col/col8276/index.html",
        api_hint="国网山西 / sx.sgcc.com.cn",
        notes="国网内网，可能无法直接访问",
        priority=5,
    ),
    "四川": ProvinceSource(
        province="四川",
        short_code="川",
        exchange_name="四川电力交易中心",
        website="https://www.sc.sgcc.com.cn",
        disclosure_url="https://www.sc.sgcc.com.cn/html/www/col/col8276/index.html",
        api_hint="国网四川 / sc.sgcc.com.cn",
        notes="国网内网，可能无法直接访问",
        priority=4,
    ),
    "安徽": ProvinceSource(
        province="安徽",
        short_code="皖",
        exchange_name="安徽电力交易中心",
        website="https://www.ah.sgcc.com.cn",
        disclosure_url="https://www.ah.sgcc.com.cn/html/www/col/col8276/index.html",
        api_hint="国网安徽 / ah.sgcc.com.cn",
        notes="国网内网，可能无法直接访问",
        priority=3,
    ),
    "福建": ProvinceSource(
        province="福建",
        short_code="闽",
        exchange_name="福建电力交易中心",
        website="https://www.fj.sgcc.com.cn",
        disclosure_url="https://www.fj.sgcc.com.cn/html/www/col/col8276/index.html",
        api_hint="国网福建 / fj.sgcc.com.cn",
        notes="国网内网，可能无法直接访问",
        priority=3,
    ),
    "河南": ProvinceSource(
        province="河南",
        short_code="豫",
        exchange_name="河南电力交易中心",
        website="https://www.ha.sgcc.com.cn",
        disclosure_url="https://www.ha.sgcc.com.cn/html/www/col/col8276/index.html",
        api_hint="国网河南 / ha.sgcc.com.cn",
        notes="国网内网，可能无法直接访问",
        priority=3,
    ),
    "湖北": ProvinceSource(
        province="湖北",
        short_code="鄂",
        exchange_name="湖北电力交易中心",
        website="https://www.hb.sgcc.com.cn",
        disclosure_url="https://www.hb.sgcc.com.cn/html/www/col/col8276/index.html",
        api_hint="国网湖北 / hb.sgcc.com.cn",
        notes="国网内网，可能无法直接访问",
        priority=3,
    ),
    "湖南": ProvinceSource(
        province="湖南",
        short_code="湘",
        exchange_name="湖南电力交易中心",
        website="https://www.hn.sgcc.com.cn",
        disclosure_url="https://www.hn.sgcc.com.cn/html/www/col/col8276/index.html",
        api_hint="国网湖南 / hn.sgcc.com.cn",
        notes="国网内网，可能无法直接访问",
        priority=2,
    ),
    "江西": ProvinceSource(
        province="江西",
        short_code="赣",
        exchange_name="江西电力交易中心",
        website="https://www.jx.sgcc.com.cn",
        disclosure_url="https://www.jx.sgcc.com.cn/html/www/col/col8276/index.html",
        api_hint="国网江西 / jx.sgcc.com.cn",
        notes="国网内网，可能无法直接访问",
        priority=2,
    ),
    "蒙西": ProvinceSource(
        province="蒙西",
        short_code="蒙西",
        exchange_name="内蒙古电力交易中心",
        website="https://www.impc.com.cn",
        disclosure_url="https://www.impc.com.cn/publication/transaction",
        api_hint="内蒙古电力集团 / impc.com.cn",
        notes="独立电网，可能有访问限制",
        priority=4,
    ),
    "甘肃": ProvinceSource(
        province="甘肃",
        short_code="甘",
        exchange_name="甘肃电力交易中心",
        website="https://www.gs.sgcc.com.cn",
        disclosure_url="https://www.gs.sgcc.com.cn/html/www/col/col8276/index.html",
        api_hint="国网甘肃 / gs.sgcc.com.cn",
        notes="国网内网，可能无法直接访问",
        priority=3,
    ),
    "新疆": ProvinceSource(
        province="新疆",
        short_code="新",
        exchange_name="新疆电力交易中心",
        website="https://www.xj.sgcc.com.cn",
        disclosure_url="https://www.xj.sgcc.com.cn/html/www/col/col8276/index.html",
        api_hint="国网新疆 / xj.sgcc.com.cn",
        notes="国网内网，可能无法直接访问",
        priority=2,
    ),
    "云南": ProvinceSource(
        province="云南",
        short_code="滇",
        exchange_name="云南电力交易中心",
        website="https://www.yn.sgcc.com.cn",
        disclosure_url="https://www.yn.sgcc.com.cn/html/www/col/col8276/index.html",
        api_hint="国网云南 / yn.sgcc.com.cn",
        notes="国网内网，可能无法直接访问",
        priority=3,
    ),
    "贵州": ProvinceSource(
        province="贵州",
        short_code="黔",
        exchange_name="贵州电力交易中心",
        website="https://www.gz.sgcc.com.cn",
        disclosure_url="https://www.gz.sgcc.com.cn/html/www/col/col8276/index.html",
        api_hint="国网贵州 / gz.sgcc.com.cn",
        notes="国网内网，可能无法直接访问",
        priority=2,
    ),
    "陕西": ProvinceSource(
        province="陕西",
        short_code="陕",
        exchange_name="陕西电力交易中心",
        website="https://www.sn.sgcc.com.cn",
        disclosure_url="https://www.sn.sgcc.com.cn/html/www/col/col8276/index.html",
        api_hint="国网陕西 / sn.sgcc.com.cn",
        notes="国网内网，可能无法直接访问",
        priority=3,
    ),
    "上海": ProvinceSource(
        province="上海",
        short_code="沪",
        exchange_name="上海电力交易中心",
        website="https://pmos.sh.sgcc.com.cn",
        disclosure_url="https://pmos.sh.sgcc.com.cn/pxf-settlement-outnetpub/",
        api_hint="上海电力交易 / pmos.sh.sgcc.com.cn",
        notes="可能有访问限制",
        priority=4,
    ),
}


# 已知的公开第三方数据聚合平台（可爬取）
THIRD_PARTY_SOURCES = {
    "亿电": "https://www.yd380v.com",
    "电查查": "https://www.dianchacha.cn",
    "泛能网": "https://etpage.fanneng.com",
}


# 全国性公开数据来源
NATIONAL_SOURCES = {
    "国家能源局": "https://www.nea.gov.cn",
    "中电联": "https://www.cec.org.cn",
    "全国煤炭交易中心": "https://www.nccoal.com",
}


def get_accessible_provinces() -> list[str]:
    """返回可以尝试直接访问的省份列表"""
    return ["广东", "山东", "山西", "浙江", "江苏", "上海"]


def get_all_provinces() -> list[str]:
    """返回所有已配置省份列表"""
    return list(PROVINCE_SOURCES.keys())
