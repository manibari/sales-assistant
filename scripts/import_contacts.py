"""Batch import contacts from structured list into Nexus CRM.

Usage: python scripts/import_contacts.py [--dry-run]
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import get_connection

# ---------------------------------------------------------------------------
# Raw contact data — parsed from user input
# ---------------------------------------------------------------------------

CONTACTS = [
    # (company, name, department, title, phone, email, referral, industry)
    ("辛耘", "Sting", None, "CIO", None, None, "LINE", "semiconductor"),
    ("日月光", "潔西卡", "IT", "經理", None, None, None, "semiconductor"),
    ("華泰", "王金秋 Daniel", None, "CIO", None, "Daniel_Wang@ose.com.tw", None, "semiconductor"),
    ("矽格", "TT", None, "CIO", "931288885", "tt_huang@utc.com.tw", None, "semiconductor"),
    ("群創", "蕭立應", "南科TFT第五總廠", "廠長", None, "ly.hsiao@innolux.com", None, "semiconductor"),
    ("群創", "廖健宏", "總經理辦公室", "協理", None, "jh.liao@innolux.com", None, "semiconductor"),
    ("SDP", "Hank", None, "IT協理", None, None, "LINE", "semiconductor"),
    ("敏實", None, None, None, None, None, "Harold", "manufacturing"),
    ("南茂", "邱鈺程", "系統工程管理處", "處長", None, "peter_chiu@chipmos.com", None, "semiconductor"),
    ("聯詠", "施明賢 Jim", None, "資深副處長", None, "jim_shih@novatek.com.tw", None, "semiconductor"),
    ("欣興電", "李品辰", "智能工廠處", "經理", None, "PinChen_Lee@unimicron.com", None, "semiconductor"),
    ("景碩", "顏景芳", None, "CIO", None, "roger.cf.yen@kinsus.com.tw", None, "semiconductor"),
    ("台光電", "Cruise.jen", None, None, None, "Cruise.jen@mail.emctw.com", None, "semiconductor"),
    ("台虹", "East", None, None, None, None, "LINE", "semiconductor"),
    ("楠梓電", "Ck Chen", None, "CEO President", None, "ck_chen@wuspc.com", None, "semiconductor"),
    ("同欣電", "鄭博修", None, "協理", None, "pohsiu.cheng@theil.com", None, "semiconductor"),
    ("東山精密", None, None, None, None, None, "Harold", "manufacturing"),
    ("福盈化學", "李宗任", None, "廠長", None, "tony.lee@jintex.com.tw", None, "petrochemical"),
    ("福盈化學", "林瑪莉", "研發中心智財處", "協理", None, "mary.lin@jintex.com.tw", None, "petrochemical"),
    ("長興材料", "林俊良", "製程技術部", "部長", None, "cl_chen@eternal-group.com", None, "petrochemical"),
    ("長春人造樹脂", "毛薇婷", "研發部", "工程師", None, "weiting_mao@ccpgp.com", None, "petrochemical"),
    ("永光", "陳坤木", None, "廠長", None, "11703@ecic.com.tw", None, "petrochemical"),
    ("永光", "陳克倫", None, "研發副總", None, "colline@ecic.com.tw", None, "petrochemical"),
    ("永光", "林昭文", "電化事業處", "副總經理", None, "asap@ecic.com.tw", None, "petrochemical"),
    ("三芳", "鄭國光", "總經理室", "副總經理", None, "ckk@sanfang.com.tw", None, "manufacturing"),
    ("三芳", "泫州蔡", "經營管理處", "副協理", None, "hct@sanfang.com.tw", None, "manufacturing"),
    ("德淵", "鄭玉慧", "研發中心/特化研發處", "經理", None, "joannec@texyear.com", None, "petrochemical"),
    ("德淵", "蕭向志", None, "董事長/執行長", None, "donaldh@texyear.com", None, "petrochemical"),
    ("大立高分子", None, None, None, None, None, "Kenny", "petrochemical"),
    ("南寶", "沈永清", None, "研發副總", None, "sheenyc@nanpao.com", None, "petrochemical"),
    ("南寶", "郭沛益", "資訊部", "協理", None, "ted.kuo@nanpao.com", None, "petrochemical"),
    ("聯華製粉", "紀廠長", None, None, None, None, "LINE", "food"),
    ("聯成化科", "徐志曉", "工程企劃部", "協理", None, "chhsu@upc.com.tw", None, "petrochemical"),
    ("上緯", "陳俊安", "研發處", "協理", None, "NW384@swancor.com", None, "petrochemical"),
    ("誠美材", None, None, None, None, None, "Kenny", "petrochemical"),
    ("明基材", "Jason", None, None, None, None, "LINE", "manufacturing"),
    ("大陸恆美材", None, None, None, None, None, "維信", "manufacturing"),
    ("東聯", None, None, None, None, None, "Wei", "petrochemical"),
    ("華夏玻璃", "廖冠傑", None, "執行長", None, "richard.k.liao@hwahsiaglass.com.tw", None, "manufacturing"),
    ("華夏玻璃", "廖唯傑", None, "副執行長", None, "winston.w.liao@hwahsiaglass.com.tw", None, "manufacturing"),
    ("台玻", "林嘉佑", None, "總經理", None, "richardlin@taiwanglass.com", None, "manufacturing"),
    ("四維", "林德培", None, "董事", None, "drtplin@gmail.com", None, "manufacturing"),
    ("明基電通", "Steven", None, None, None, None, "LINE", "tech"),
    ("新普", "張秋櫻", None, "常淑總經理", None, "Cindy_Chang@simplo.com.cn", None, "tech"),
    ("新普", "宋福祥", None, "董事長兼總經理", None, "Raymond_Sung@simplo.com.tw", None, "tech"),
    ("鑫創", "許育瑞", None, "總經理", None, "kevin@sintrones.com", None, "tech"),
    ("明泰", "陳新民", None, None, None, None, "LINE", "tech"),
    ("Garmin", "Ken", None, None, None, None, "LINE", "tech"),
    ("緯穎科技", "尤焙麟 Ben", "數位創新發展處", "總監", None, "bey_yu@wiwynn.com", None, "tech"),
    ("緯穎科技", "溫宗正", None, "CIO", None, "james_wen@wiwynn.com", None, "tech"),
    ("閎康科技", "林庭楨", None, "業務經理", "918379735", "tomlin@ma-tek.com", None, "tech"),
    ("美律實業", "梁坤棠", None, "資訊副總", None, "kt.liang@merry.com.tw", None, "tech"),
    ("奇鼎科技", "鄭智文", None, "董事長", None, "steve@chd-tech.com.tw", None, "tech"),
    ("東隆", "游榮淳", None, "副理", None, "vincentyu@tloong.com.tw", None, "manufacturing"),
    ("宏遠", "柚媽", None, None, None, None, "LINE", "manufacturing"),
    ("味全", None, None, None, None, None, "Harold", "food"),
    ("玉晶光", "翁欣儀", "資訊開發部", "專案副理", None, "jessica.weng@gseo.com", None, "semiconductor"),
    ("今國光", "陳義方", None, "總經理", None, "jason@kinko-optical.com", None, "manufacturing"),
    ("大立光", "翁樑傑", "研發部", "副處長", None, "liangjaywong@largan.com.tw", None, "semiconductor"),
    ("亞洲光學", "林泰朗", None, "董事長", None, "albertlin@aoci.com.tw", None, "manufacturing"),
    ("中國砂輪", "謝榮哲", None, "執行長CEO", None, "thomas@kinik.com.tw", None, "manufacturing"),
    ("中國砂輪", "姚國慶", None, "執行長特助", None, "kevin@kinik.com.tw", None, "manufacturing"),
    ("漢翔", "蔡宗哲", "創新研發中心", "副研發長", None, "chungjertsai@ms.aidc.com.tw", None, "manufacturing"),
    ("漢翔", "莊秀美", None, "副總", None, "jemniferchuang@ms.aidc.com.tw", None, "manufacturing"),
    ("漢翔", "陳石坤", "資訊處綜合資訊組", "組長", None, "skchen@ms.aidc.com.tw", None, "manufacturing"),
    ("遠東新", "李弘暉", None, "協理", None, "hhlee@fenc.com", None, "manufacturing"),
    ("正隆", "張清標", None, "總經理", None, "charleschang@mail.clc.com.tw", None, "manufacturing"),
    ("正隆", "劉正光", None, "CIO", None, "paulliu@mail.clc.com.tw", None, "manufacturing"),
    ("廣源", "宗瀚", None, None, None, None, "LINE", "manufacturing"),
    ("順達", "美玲", None, None, None, None, "LINE", "tech"),
    ("加百裕", "Allen", None, None, None, None, "LINE", "tech"),
    ("南港輪胎", None, "RD", None, None, None, "LINE", "manufacturing"),
    ("正新輪胎", "Justin", None, "CIO", None, "justinchen@tw.maxxis.com", None, "manufacturing"),
    ("建大輪胎", "李總", None, None, None, None, "LINE", "manufacturing"),
    ("巧新", "黃聰榮", None, "董事長CEO", None, "jung@superalloy.tw", None, "manufacturing"),
    ("巧新", "黃冠賓", None, "副總經理及歐洲區總經理", None, "ben.huang@superalloy.tw", None, "manufacturing"),
    ("勝品電通", "李宏銘", None, "CEO&Founder", None, "allan.lee@topviewcorp.com", None, "tech"),
    ("勝品電通", "林貞宏", None, "總經理", None, "sadahiro.lin@topviewcorp.com", None, "tech"),
    ("視陽", "Richard", None, "CIO", None, None, "LINE", "tech"),
    ("連展", "郭迺文", None, "資深特別助理", None, "grand.kuo@aeon-holding.com", None, "manufacturing"),
    ("正崴", "周炳坤", None, "副總經理", None, "pk_chou@foxlink.com", None, "tech"),
    ("正崴", "許文彬", None, "副總經理", None, "wanson_hsu@foxlink.com", None, "tech"),
    ("信邦", "林育琦", "研究/研發", None, None, "sannylin@sinbon.com", None, "tech"),
    ("台灣晶技", "邢玉蓮", "資訊", "副處長", None, "yulienxing@txc.com.tw", None, "semiconductor"),
    ("力積電", "王瑞慶", "資訊", "副處長", None, "willwang@powerchip.com", None, "semiconductor"),
    ("五崧捷運", "邱承緯 Kenny", None, "副總經理", None, "cwchiu@shuttle.com.tw", None, "tech"),
    ("瑞鼎", None, None, None, None, None, "Kenny", "semiconductor"),
    ("鈺創", "詹敦智", "資訊處", "資深處長", None, "djchan@etron.com.tw", None, "semiconductor"),
    ("ATP華騰", "張德瑩", "SBP", "協理", None, "crystalchang@tw.atpinc.com", None, "tech"),
    ("華新麗華", "賴茂助", "不銹鋼事業群智能製造推動", "處長", None, "amos_lai@walsin.com", None, "manufacturing"),
    ("華新麗華", "牛繼聖", None, "總經理", None, "kevin_niu@walsin.com", None, "manufacturing"),
    ("華新麗華", "吳明機", "數位智能發展組織", "總經理", None, "sam_wu@walsin.com", None, "manufacturing"),
]


# ---------------------------------------------------------------------------
# Derive company websites from email domains
# ---------------------------------------------------------------------------

_PERSONAL_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com"}


def domain_to_website(email: str | None) -> str | None:
    if not email:
        return None
    domain = email.split("@")[-1].lower()
    if domain in _PERSONAL_DOMAINS:
        return None
    # Strip subdomains like "mail.", "ms.", "tw."
    parts = domain.split(".")
    if len(parts) > 2:
        if parts[0] in ("mail", "ms", "tw"):
            domain = ".".join(parts[1:])
    return f"https://www.{domain}"


def build_company_map() -> dict[str, dict]:
    """Group contacts by company, derive website."""
    companies: dict[str, dict] = {}
    for company, name, dept, title, phone, email, referral, industry in CONTACTS:
        if company not in companies:
            companies[company] = {
                "name": company,
                "industry": industry,
                "website": None,
                "contacts": [],
                "referral": None,
            }
        if email and not companies[company]["website"]:
            companies[company]["website"] = domain_to_website(email)
        if referral and not companies[company]["referral"]:
            companies[company]["referral"] = referral
        if name:
            companies[company]["contacts"].append({
                "name": name,
                "department": dept,
                "title": title,
                "phone": phone,
                "email": email,
                "referral": referral,
            })
    return companies


# ---------------------------------------------------------------------------
# Import to DB
# ---------------------------------------------------------------------------


def find_or_create_client(cur, name: str, industry: str | None, website: str | None) -> int:
    """Find existing client by name or create new one."""
    cur.execute(
        "SELECT id FROM nx_client WHERE LOWER(name) = LOWER(%s)",
        (name,),
    )
    row = cur.fetchone()
    if row:
        client_id = row[0]
        # Update industry/website if missing
        updates = []
        params = []
        if industry:
            updates.append("industry = COALESCE(industry, %s)")
            params.append(industry)
        if website:
            updates.append("notes = COALESCE(notes, '') || CASE WHEN notes IS NULL OR notes = '' THEN %s ELSE '' END")
            params.append(f"\nWebsite: {website}")
        if updates:
            params.append(client_id)
            cur.execute(
                f"UPDATE nx_client SET {', '.join(updates)} WHERE id = %s",
                params,
            )
        return client_id

    cur.execute(
        """INSERT INTO nx_client (name, industry, status, notes)
           VALUES (%s, %s, 'active', %s)
           RETURNING id""",
        (name, industry, f"Website: {website}" if website else None),
    )
    return cur.fetchone()[0]


def find_or_create_contact(cur, client_id: int, contact: dict) -> int | None:
    """Find existing contact or create new one."""
    if not contact.get("name"):
        return None

    cur.execute(
        """SELECT id FROM nx_contact
           WHERE org_type = 'client' AND org_id = %s AND LOWER(name) = LOWER(%s)""",
        (client_id, contact["name"]),
    )
    row = cur.fetchone()
    if row:
        # Update fields if empty
        contact_id = row[0]
        updates = []
        params = []
        if contact.get("title"):
            updates.append("title = COALESCE(NULLIF(title, ''), %s)")
            params.append(contact["title"])
        if contact.get("email"):
            updates.append("email = COALESCE(NULLIF(email, ''), %s)")
            params.append(contact["email"])
        if contact.get("phone"):
            updates.append("phone = COALESCE(NULLIF(phone, ''), %s)")
            params.append(contact["phone"])
        if contact.get("department"):
            updates.append("role = COALESCE(NULLIF(role, ''), %s)")
            params.append(contact["department"])
        if updates:
            params.append(contact_id)
            cur.execute(
                f"UPDATE nx_contact SET {', '.join(updates)} WHERE id = %s",
                params,
            )
        return contact_id

    cur.execute(
        """INSERT INTO nx_contact (org_type, org_id, name, title, email, phone, role)
           VALUES ('client', %s, %s, %s, %s, %s, %s)
           RETURNING id""",
        (
            client_id,
            contact["name"],
            contact.get("title"),
            contact.get("email"),
            contact.get("phone"),
            contact.get("department"),
        ),
    )
    return cur.fetchone()[0]


def main():
    dry_run = "--dry-run" in sys.argv
    companies = build_company_map()

    print(f"解析完成：{len(companies)} 家公司, {sum(len(c['contacts']) for c in companies.values())} 位聯絡人\n")

    # Print summary table
    print(f"{'公司':<16} {'產業':<14} {'聯絡人':<4} {'網站':<40} {'引薦'}")
    print("-" * 100)
    for co in companies.values():
        website = co["website"] or ""
        referral = co["referral"] or ""
        print(f"{co['name']:<16} {co['industry']:<14} {len(co['contacts']):<4} {website:<40} {referral}")

    if dry_run:
        print("\n[DRY RUN] 不執行匯入")
        return

    print("\n開始匯入...")
    from database.connection import init_db
    init_db()

    stats = {"clients_created": 0, "clients_matched": 0, "contacts_created": 0, "contacts_matched": 0}

    with get_connection() as conn:
        with conn.cursor() as cur:
            for co in companies.values():
                # Check if client exists
                cur.execute(
                    "SELECT id FROM nx_client WHERE LOWER(name) = LOWER(%s)",
                    (co["name"],),
                )
                existed = cur.fetchone() is not None

                client_id = find_or_create_client(
                    cur, co["name"], co["industry"], co["website"]
                )
                if existed:
                    stats["clients_matched"] += 1
                else:
                    stats["clients_created"] += 1

                for contact in co["contacts"]:
                    cur.execute(
                        """SELECT id FROM nx_contact
                           WHERE org_type = 'client' AND org_id = %s AND LOWER(name) = LOWER(%s)""",
                        (client_id, contact["name"]),
                    )
                    contact_existed = cur.fetchone() is not None

                    find_or_create_contact(cur, client_id, contact)
                    if contact_existed:
                        stats["contacts_matched"] += 1
                    else:
                        stats["contacts_created"] += 1

    print(f"\n✅ 匯入完成")
    print(f"  客戶：{stats['clients_created']} 新建 / {stats['clients_matched']} 已存在")
    print(f"  聯絡人：{stats['contacts_created']} 新建 / {stats['contacts_matched']} 已存在")


if __name__ == "__main__":
    main()
