"""Seed script — clear all dummy data, import real CRM contacts.

Reads ~72 contacts, groups by company, assigns decision_maker / champions
based on title seniority, and inserts ~34 CRM records with data_year = 2025.
"""

import sys
import os
from collections import defaultdict

# Ensure project root is in path when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from psycopg2.extras import Json

from database.connection import init_db, get_connection

# ---------------------------------------------------------------------------
# Raw contact data (from TSV import)
# ---------------------------------------------------------------------------

_RAW_CONTACTS = [
    {"company": "三芳化學", "dept": "經營管理處", "title": "副協理", "first": "泫州", "last": "蔡", "email": "hct@sanfang.com.tw", "phone": "073712111", "mobile": "", "ext": ""},
    {"company": "大立高分子工業股份有限公司", "dept": "", "title": "總經理", "first": "文忠", "last": "楊", "email": "dlvipd@mail.daily-polymer.com", "phone": "(07)622-1345", "mobile": "", "ext": ""},
    {"company": "大立高分子工業股份有限公司", "dept": "", "title": "副總經理", "first": "易展", "last": "李", "email": "dlgl10@mail.daily-polymer.com", "phone": "(07)225-7200", "mobile": "", "ext": "261"},
    {"company": "大立高分子工業股份有限公司", "dept": "新材料專業部 營業處", "title": "處長", "first": "志桓", "last": "邵", "email": "dles10@mail.daily-polymer.com", "phone": "(07)622-1345", "mobile": "0936-522-599", "ext": "232"},
    {"company": "大宇纺織股份有限公司", "dept": "工業4.0推展計畫辦公室", "title": "經理", "first": "芳誠", "last": "許", "email": "rickshue@universal-tex.com", "phone": "(02) 2552-3977", "mobile": "0933-200560", "ext": "707"},
    {"company": "弓銓企業股份有限公司", "dept": "生產部", "title": "副理", "first": "享容", "last": "鍾", "email": "a01059@ems.com.tw", "phone": "06-505-7270", "mobile": "", "ext": "332"},
    {"company": "弓銓企業股份有限公司", "dept": "生產部", "title": "", "first": "爵宇", "last": "吳", "email": "a09011@ems.com.tw", "phone": "(06)505-7270", "mobile": "", "ext": "331"},
    {"company": "中日合成化學股份有限公司", "dept": "管理部門 管理部", "title": "資訊課 課長", "first": "坤龍", "last": "鍾", "email": "sinockl@sjc.com.tw", "phone": "(02)2396-6223", "mobile": "", "ext": "236"},
    {"company": "中日合成化學股份有限公司", "dept": "營業技術部門", "title": "協理", "first": "義邦", "last": "盧", "email": "lo1207@sjc.com.tw", "phone": "(02)2396-6223", "mobile": "0910-076-161", "ext": "246"},
    {"company": "太康精密股份有限公司", "dept": "", "title": "董事長兼總經理", "first": "辛池", "last": "葉", "email": "Daniel_Yeh@t-conn.com", "phone": "886-2-2698-3890", "mobile": "", "ext": "1100"},
    {"company": "台強電機股份有限公司", "dept": "", "title": "經理", "first": "保言", "last": "林", "email": "paoyenlin@tc-power.com", "phone": "886-6-2543816~7", "mobile": "", "ext": ""},
    {"company": "台灣佳能資訊股份有限公司", "dept": "BIS行銷企劃事業處 BIS行銷企劃部", "title": "產品/市場行銷企劃經理", "first": "紹祺", "last": "李", "email": "chuck_ee@mtw.canon.com.tw", "phone": "(02)6632 1858", "mobile": "0928-817506", "ext": ""},
    {"company": "台灣佳能資訊股份有限公司", "dept": "BIS行銷企劃事業處 BIS新事業發展部", "title": "副總經理", "first": "友三", "last": "王", "email": "dennis_wn@mtw.canon.com.tw", "phone": "(02)66328888", "mobile": "(02)6632 1932", "ext": ""},
    {"company": "台灣佳能資訊股份有限公司", "dept": "BIS市場行銷企劃部", "title": "產品行銷企劃副理", "first": "智超", "last": "張", "email": "michael_chang@cmtw.canon.com.tw", "phone": "(02)6632 1908", "mobile": "0930-869755", "ext": ""},
    {"company": "台灣佳能資訊股份有限公司", "dept": "BIS行銷與新產品事業處 BIS企劃部", "title": "副主任", "first": "啟康", "last": "丁", "email": "chris_ting@mtw.canon.com.tw", "phone": "(02)66321864", "mobile": "0987-807873", "ext": ""},
    {"company": "正美企業股份有限公司", "dept": "製造部", "title": "資深經理", "first": "嘉宏", "last": "魏", "email": "jiahong@cymmetrik.com", "phone": "", "mobile": "0958-739939", "ext": ""},
    {"company": "正美企業股份有限公司", "dept": "董事長室", "title": "總經理", "first": "雪如", "last": "蔡", "email": "cherie.hr.tsai@cymmetrik.com", "phone": "886 2 2785 5600", "mobile": "", "ext": ""},
    {"company": "正淩精密工業股份有限公司", "dept": "資訊部", "title": "經理", "first": "姣燕", "last": "陳", "email": "frida.chen@nextron.com.tw", "phone": "886-2-6616-2000", "mobile": "", "ext": "870"},
    {"company": "正淩精密工業股份有限公司", "dept": "資訊部", "title": "副理", "first": "啟泰", "last": "黃", "email": "chitai.huang@nextron.com.tw", "phone": "886-2-6616-2000", "mobile": "0910-203-575", "ext": "868"},
    {"company": "正新橡膠工業股份有限公司", "dept": "資訊部 & 二代", "title": "協理", "first": "柏嘉", "last": "陳", "email": "JustinChen@tw.maxxis.com", "phone": "886-4-8525151", "mobile": "", "ext": "125"},
    {"company": "丞易國際貿易有限公司", "dept": "", "title": "總經理", "first": "珀琳", "last": "蘇", "email": "paulsu@paralucent.com.tw", "phone": "(07)5368231", "mobile": "0933-204405", "ext": ""},
    {"company": "丞易國際貿易有限公司", "dept": "", "title": "軟體工程師", "first": "昱瑄", "last": "蘇", "email": "michaelsu@paralux.com.tw", "phone": "(07)5368231", "mobile": "0968-909433", "ext": ""},
    {"company": "全一電子股份有限公司", "dept": "數智轉型部", "title": "副理", "first": "仲銘", "last": "吳", "email": "johnny@ccy.im", "phone": "06-2647622", "mobile": "", "ext": "351"},
    {"company": "全一電子股份有限公司", "dept": "改善部", "title": "專案經理", "first": "志文", "last": "王", "email": "kevin.wang@jebsee.com.tw", "phone": "06-3000968", "mobile": "", "ext": "824"},
    {"company": "旭源包裝科技股份有限公司", "dept": "", "title": "總經理", "first": "雅萍", "last": "莊", "email": "rita@xuyuanpack.com", "phone": "03-5982727", "mobile": "", "ext": ""},
    {"company": "旭源包裝科技股份有限公司", "dept": "總經理室", "title": "特助", "first": "盛宏", "last": "黃", "email": "michael.huang@xuyuanpack.com", "phone": "05-2952888", "mobile": "", "ext": "1115"},
    {"company": "旭源包裝科技股份有限公司", "dept": "", "title": "財務長", "first": "素鍰", "last": "楊", "email": "angela.yang@xuyuanpack.com", "phone": "03-5982727", "mobile": "", "ext": ""},
    {"company": "旭源包裝科技股份有限公司", "dept": "資訊部", "title": "資深工程師", "first": "銘樟", "last": "顏", "email": "irk.yen@xuyuanpack.com", "phone": "03-5982727", "mobile": "0928-849167", "ext": "1613"},
    {"company": "宏致電子股份有限公司", "dept": "", "title": "資訊長", "first": "玉梅", "last": "鄭", "email": "sindy@acesconn.com", "phone": "886-3-4632808", "mobile": "886-928-254-963", "ext": "1305"},
    {"company": "宏致電子股份有限公司", "dept": "總經理室", "title": "", "first": "欣衛", "last": "林", "email": "grandlin@acesconn.com", "phone": "886-3-463-2808", "mobile": "", "ext": "2341"},
    {"company": "町洋企業股份有限公司", "dept": "", "title": "集團資訊長", "first": "德元", "last": "王", "email": "mark.wang@dinkle.com", "phone": "886-2-8069-9000", "mobile": "", "ext": "1320"},
    {"company": "東隆興業股份有限公司", "dept": "", "title": "副理", "first": "榮淳", "last": "游", "email": "vincentyu@tloong.com.tw", "phone": "(02)2961-2112", "mobile": "", "ext": "134"},
    {"company": "東隆興業股份有限公司", "dept": "", "title": "", "first": "閎智", "last": "游", "email": "", "phone": "(02)2961-2112", "mobile": "", "ext": "224"},
    {"company": "花仙子企業集團", "dept": "全球供應中心", "title": "副總經理", "first": "鴻偉", "last": "林", "email": "honweilin@farcent.com.tw", "phone": "02-2592-2860", "mobile": "0953-225433", "ext": "1300"},
    {"company": "花仙子企業集團", "dept": "", "title": "集團副董事長", "first": "佳郁", "last": "王", "email": "anwang@farcent.com.tw", "phone": "02-2592-2860", "mobile": "", "ext": "1151"},
    {"company": "金晶國際股份有限公司", "dept": "先進事業處", "title": "專員", "first": "馨雅", "last": "郭", "email": "sunnya@chin-ching.com.tw", "phone": "886-2-25061136", "mobile": "0900-131-213", "ext": "116"},
    {"company": "金晶國際股份有限公司", "dept": "資訊處", "title": "資訊主任", "first": "于峻", "last": "羅", "email": "yuchun@chin-ching.com.tw", "phone": "886-2-25061136", "mobile": "0977-168-994", "ext": "327"},
    {"company": "金晶國際股份有限公司", "dept": "資訊處", "title": "處長", "first": "玲玲", "last": "謝", "email": "linda.hsieh@chin-ching.com.tw", "phone": "886-2-25061136", "mobile": "0922-920-321", "ext": "321"},
    {"company": "長春人造樹脂", "dept": "應用發展本部", "title": "窗口", "first": "章絜鈞", "last": "", "email": "jiejiun_chang@ccpgp.com", "phone": "", "mobile": "0975406577", "ext": ""},
    {"company": "長春人造樹脂", "dept": "研發部", "title": "課長", "first": "鄭博元", "last": "", "email": "po_yuan_cheng@ccpgp.com", "phone": "073711301501", "mobile": "", "ext": ""},
    {"company": "信盛精工股份有限公司", "dept": "技術部", "title": "經理", "first": "俊賢", "last": "余", "email": "jiunn@stm.com.tw", "phone": "886-7-628-3172", "mobile": "", "ext": "245"},
    {"company": "胡連精密股份有限公司", "dept": "全球生產事業群 運籌處", "title": "經理", "first": "春菊", "last": "徐", "email": "daisy@hulane.com.tw", "phone": "02-2694-0551", "mobile": "", "ext": "13002"},
    {"company": "恩良企業股份有限公司", "dept": "", "title": "副總經理", "first": "榮瑩", "last": "鄭", "email": "yingying@enliang.com.tw", "phone": "(03)598-4207", "mobile": "", "ext": "104"},
    {"company": "翊聖企業股份有限公司", "dept": "品技部技術課", "title": "副課長", "first": "信結", "last": "羅", "email": "losj@fap.com.tw", "phone": "886-3-371-2368", "mobile": "", "ext": ""},
    {"company": "翊聖企業股份有限公司", "dept": "新事業部", "title": "經理", "first": "志謙", "last": "林", "email": "dominiclin@fap.com.tw", "phone": "886-3-371-2368", "mobile": "", "ext": ""},
    {"company": "閎康科技", "dept": "總經理室", "title": "特助", "first": "育全", "last": "呂", "email": "albertlu@matek.com", "phone": "886-3-611-6678", "mobile": "886-970-110-928", "ext": "4601"},
    {"company": "雅文塑膠", "dept": "工程部", "title": "經理", "first": "繼松", "last": "黃", "email": "yeasen.model@msa.hinet.net", "phone": "886-2-8521-3611-3", "mobile": "886-937-037-962", "ext": ""},
    {"company": "雅文塑膠股份有限公司", "dept": "", "title": "特助", "first": "創宇", "last": "張", "email": "ccu@yeawen.com.tw", "phone": "886-2-85213611-3", "mobile": "", "ext": ""},
    {"company": "新揚科技股份有限公司", "dept": "", "title": "總經理", "first": "介宏", "last": "吳", "email": "Jay.Wu@thinflex.com.tw", "phone": "(07)695-5236", "mobile": "", "ext": ""},
    {"company": "新揚科技股份有限公司", "dept": "總經理室", "title": "經營企劃室特助", "first": "世正", "last": "廖", "email": "danny.liao@thinflex.com.tw", "phone": "(07)695-5236", "mobile": "0939 422 511", "ext": "2365"},
    {"company": "福盈科技化學", "dept": "集團研發中心 PhD", "title": "協理", "first": "陳若君", "last": "", "email": "jochun.chen@jintex.com.tw", "phone": "88633869968,,501", "mobile": "", "ext": ""},
    {"company": "福盈科技化學", "dept": "集團供應鏈中心", "title": "副總經理", "first": "蔡淑芬", "last": "", "email": "dinah.tsai@jintex-chemical.com", "phone": "886225788999,,308", "mobile": "0928769132", "ext": ""},
    {"company": "戴思科技股份有限公司", "dept": "機構開發部研發", "title": "經理", "first": "子洋", "last": "白", "email": "brianpai@dasitek.com.tw", "phone": "06-2792886", "mobile": "0970-139-662", "ext": ""},
    {"company": "鴻呈實業股份有限公司", "dept": "", "title": "協理", "first": "靜瑜", "last": "簡", "email": "ching_yu@vso-corp.com", "phone": "886-2-3234-3038", "mobile": "0955-919-129", "ext": "104"},
    {"company": "鴻呈實業股份有限公司", "dept": "", "title": "董事長", "first": "忠正", "last": "簡", "email": "", "phone": "886-2-3234-3038", "mobile": "", "ext": ""},
    {"company": "鴻呈實業股份有限公司", "dept": "", "title": "總經理", "first": "星宏", "last": "林", "email": "star.lin@vso-corp.com", "phone": "886-2-3234-3038", "mobile": "", "ext": "101"},
    {"company": "鴻呈實業股份有限公司", "dept": "", "title": "資訊長", "first": "朝崇", "last": "莊", "email": "allan@vso.com.tw", "phone": "886-2-3234-3038", "mobile": "", "ext": "179"},
    {"company": "寶成工業股份有限公司", "dept": "", "title": "專案裏理", "first": "慧娟", "last": "陳", "email": "jenny.chen1225@pouchen.com", "phone": "886-4-24615678", "mobile": "886-918-259316", "ext": "6728"},
    {"company": "寶成工業股份有限公司", "dept": "", "title": "經理", "first": "美旭", "last": "陳", "email": "lorraine.chen@pouchen.com", "phone": "886-4-24615678", "mobile": "886-905-731777", "ext": "6722"},
    {"company": "寶成工業股份有限公司", "dept": "全球供應鏈管理總部", "title": "工程師", "first": "晏誠", "last": "梁", "email": "jordan.liang@pouchen.com", "phone": "886-4-7683506", "mobile": "886-988-855689", "ext": "3276"},
    {"company": "寶成工業股份有限公司", "dept": "全球供應鏈管理總部", "title": "副協理", "first": "啟智", "last": "洪", "email": "Brian_Hung@pouchen.com", "phone": "886-4-7683506", "mobile": "886-921234012", "ext": "3277"},
    {"company": "康那香企業股份有限公司", "dept": "BA_集團營運業務分析師", "title": "總經理室", "first": "志偉", "last": "邱", "email": "marco.chiu@knh-global.com", "phone": "02-23459909", "mobile": "", "ext": "2906"},
    {"company": "康那香企業股份有限公司", "dept": "海外暨衛用專案業務中心", "title": "副總經理", "first": "沛宏", "last": "林", "email": "glen.l@knh-global.com", "phone": "02-23459909", "mobile": "", "ext": "2688"},
    {"company": "康那香企業股份有限公司", "dept": "總經理室", "title": "專員", "first": "庭維", "last": "吳", "email": "brian.wu@knh-global.com", "phone": "02-23459909", "mobile": "", "ext": "2283"},
    {"company": "卡雨蔡司股份有限公司台北分公司", "dept": "IT Manager", "title": "IT Manager", "first": "聰憲", "last": "郭", "email": "lennon.kuo@zeiss.com", "phone": "", "mobile": "", "ext": ""},
    {"company": "卡雨蔡司股份有限公司台北分公司", "dept": "", "title": "Head of Business Operation Head of Sales Operation", "first": "偉安", "last": "張", "email": "gabriel.cheung@zeiss.com", "phone": "", "mobile": "", "ext": ""},
    {"company": "卡雨蔡司股份有限公司台北分公司", "dept": "供應鏈管理", "title": "總監", "first": "家榮", "last": "莫", "email": "mike.mo@zeiss.com", "phone": "", "mobile": "", "ext": ""},
    {"company": "富堡工業股份有限公司", "dept": "", "title": "董事", "first": "峻樟", "last": "林", "email": "david.lin@fuburg.com", "phone": "(02)2356-0429", "mobile": "", "ext": ""},
    {"company": "富堡工業股份有限公司", "dept": "資訊處", "title": "專員", "first": "伊衍", "last": "戴", "email": "dennis.tar@fuburg.com", "phone": "(03)352-9862", "mobile": "", "ext": "523"},
    {"company": "富堡工業股份有限公司", "dept": "建廠廠務組", "title": "副主任", "first": "傳瓊", "last": "董", "email": "tony.tung@fuburg.com", "phone": "(03)352-9862", "mobile": "", "ext": "102"},
    {"company": "富堡工業股份有限公司", "dept": "製造部", "title": "研發主任", "first": "政龍", "last": "吳", "email": "austin.wu@fuburg.com", "phone": "(03)352-9862", "mobile": "", "ext": "220"},
    {"company": "富堡工業股份有限公司", "dept": "製造部資材課", "title": "主任", "first": "麗玉", "last": "翁", "email": "lily.weng@fuburg.com", "phone": "(03)352-9862", "mobile": "", "ext": "530"},
    {"company": "富堡工業股份有限公司", "dept": "製造部", "title": "採購副主任", "first": "宏安", "last": "簡", "email": "sean.chien@fuburg.com", "phone": "(03)352-9862", "mobile": "", "ext": "221"},
]

# Company name normalization (merge duplicates)
_COMPANY_ALIASES = {
    "雅文塑膠": "雅文塑膠股份有限公司",
}


# ---------------------------------------------------------------------------
# Title ranking (lower number = more senior)
# ---------------------------------------------------------------------------

def _rank_title(title: str) -> int:
    """Return a seniority rank for a title. Lower = more senior."""
    if not title:
        return 99
    t = title.strip()
    # Level 1: 董事長 / 副董事長
    if "董事長" in t or "副董事長" in t:
        return 1
    # Level 2: 總經理 (but not 副總經理)
    if "總經理" in t and "副總" not in t:
        return 2
    # Level 3: 副總經理 / 副總
    if "副總" in t:
        return 3
    # Level 4: 資訊長 / CIO
    if "資訊長" in t:
        return 4
    # Level 5: 協理 / 副協理
    if "協理" in t:
        return 5
    # Level 6: 處長 / 總監
    if "處長" in t or "總監" in t:
        return 6
    # Level 7: 董事 (not 董事長)
    if "董事" in t:
        return 7
    # Level 8: 財務長
    if "財務長" in t:
        return 8
    # Rest: managers, engineers, specialists, etc.
    return 99


def _clean_phone(phone: str) -> str:
    """Remove leading quote marks from phone numbers."""
    if not phone:
        return ""
    return phone.lstrip("'").strip()


def _full_name(contact: dict) -> str:
    """Build full name from last + first. If last is empty, use first directly."""
    last = (contact.get("last") or "").strip()
    first = (contact.get("first") or "").strip()
    if last:
        return f"{last}{first}"
    return first


def _contact_to_person(contact: dict) -> dict:
    """Convert a raw contact dict into a person dict for JSONB storage."""
    phone = _clean_phone(contact.get("phone", ""))
    mobile = _clean_phone(contact.get("mobile", ""))
    ext = (contact.get("ext") or "").strip()

    phone_parts = []
    if phone:
        phone_parts.append(phone)
    if ext:
        phone_parts.append(f"ext.{ext}")
    phone_str = " ".join(phone_parts)
    if mobile:
        phone_str = f"{phone_str}, {mobile}" if phone_str else mobile

    return {
        "name": _full_name(contact),
        "title": (contact.get("title") or "").strip(),
        "email": (contact.get("email") or "").strip(),
        "phone": phone_str,
        "notes": (contact.get("dept") or "").strip(),
    }


def _build_companies():
    """Group contacts by company, determine decision_maker and champions."""
    groups = defaultdict(list)
    for c in _RAW_CONTACTS:
        company = c["company"].strip()
        company = _COMPANY_ALIASES.get(company, company)
        groups[company].append(c)

    companies = []
    for company_name in sorted(groups.keys()):
        contacts = groups[company_name]
        # Sort by title rank (most senior first)
        contacts.sort(key=lambda c: _rank_title(c.get("title", "")))

        persons = [_contact_to_person(c) for c in contacts]
        decision_maker = persons[0]
        champions = persons[1:] if len(persons) > 1 else []

        # Use first contact's phone as company contact_info
        first_phone = _clean_phone(contacts[0].get("phone", ""))

        companies.append({
            "company_name": company_name,
            "decision_maker": decision_maker,
            "champions": champions,
            "contact_info": first_phone,
        })

    return companies


def seed():
    """Clear existing data and insert real CRM records."""
    init_db()

    companies = _build_companies()

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Clear in FK-safe order
            cur.execute("DELETE FROM project_task")
            cur.execute("DELETE FROM work_log")
            cur.execute("DELETE FROM sales_plan")
            cur.execute("DELETE FROM project_list")
            cur.execute("DELETE FROM crm")
            cur.execute("DELETE FROM annual_plan")
            # Reset sequences
            cur.execute("ALTER SEQUENCE project_list_project_id_seq RESTART WITH 1")
            cur.execute("ALTER SEQUENCE work_log_log_id_seq RESTART WITH 1")
            cur.execute("ALTER SEQUENCE sales_plan_plan_id_seq RESTART WITH 1")
            cur.execute("ALTER SEQUENCE project_task_task_id_seq RESTART WITH 1")

            # Insert CRM records with sequential client_id
            for idx, comp in enumerate(companies, start=1):
                client_id = f"CLI-{idx:03d}"
                cur.execute(
                    """INSERT INTO crm
                       (client_id, company_name, decision_maker, champions,
                        contact_info, data_year)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (
                        client_id,
                        comp["company_name"],
                        Json(comp["decision_maker"]),
                        Json(comp["champions"]) if comp["champions"] else None,
                        comp["contact_info"] or None,
                        2025,
                    ),
                )

    print(f"Seed data loaded successfully!")
    print(f"  - {len(companies)} clients (crm) — real contacts with data_year=2025")
    print(f"  - 0 products, 0 projects, 0 work logs, 0 sales plans, 0 tasks")
    print(f"  - app_settings preserved (ON CONFLICT DO NOTHING in schema)")


if __name__ == "__main__":
    seed()
