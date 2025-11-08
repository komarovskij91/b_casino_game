# top_snapshot.py
import time
import math
from collections import defaultdict
import random

def compare_leagues(old_league: str, new_league: str) -> bool | None:
    leagues = ["tree", "iron", "bronze", "silver", "gold", "platinum", "diamond"]

    if old_league not in leagues or new_league not in leagues:
        raise ValueError("Неверное название лиги")

    old_index = leagues.index(old_league)
    new_index = leagues.index(new_league)

    if new_index > old_index:
        return True   # новая выше
    elif new_index < old_index:
        return False  # новая ниже
    else:
        return None   # не изменилась


def build_top_snapshot(players_input,
                       prize_pool: float = 5000.0,
                       alpha: float = 1.0,
                       top_limit_per_bucket: int | None = 100) -> dict:
    """
    Вход:
        players_input: список dict: {"user": int, "point_liga": int, "name": str}

    Параметры:
        prize_pool               — общий призовой фонд ($) на распределение по подлигам
        alpha                    — резкость распределения внутри подлиги (веса ~ 1 / rank^alpha)
        top_limit_per_bucket     — сколько игроков хранить в каждой подлиге в "top"
                                   (None = хранить всех)

    Возврат:
        dict с полями "meta", "index", "leagues"
        - meta.updated_at (epoch), meta.version
        - index[<user_id>] = {league, tier, rank, points, dollar, name}
        - leagues[Лига]["1".."4"] = { total, top: [ {user_id, name, point_liga, dollar, rank}, ... ] }
    """

    # --- порядок лиг для вывода ---
    league_order = ["Алмаз", "Платина", "Золото", "Серебро", "Бронза", "Железо", "Дерево"]

    # --- % игроков по подлигам (сумма = 100) ---
    league_distribution = {
        "Дерево":   {"Дерево 1": 16.0, "Дерево 2": 9.0,  "Дерево 3": 6.0,  "Дерево 4": 4.0},   # 35%
        "Железо":   {"Железо 1": 14.0, "Железо 2": 8.0, "Железо 3": 5.0,  "Железо 4": 3.0},   # 30%
        "Бронза":   {"Бронза 1": 8.0,  "Бронза 2": 4.0, "Бронза 3": 2.0,  "Бронза 4": 1.0},   # 15%
        "Серебро":  {"Серебро 1": 5.0, "Серебро 2": 3.0,"Серебро 3": 2.0, "Серебро 4": 1.0},  # 11%
        # после Золота — обратная прогрессия (4-я подлига крупней)
        "Золото":   {"Золото 4": 3.0,  "Золото 3": 1.5, "Золото 2": 1.0,  "Золото 1": 0.5},  # 6%
        "Платина":  {"Платина 4": 1.0, "Платина 3": 0.5,"Платина 2": 0.35,"Платина 1": 0.15},# 2%
        "Алмаз":    {"Алмаз 4": 0.5,   "Алмаз 3": 0.3,  "Алмаз 2": 0.15,  "Алмаз 1": 0.05},  # 1%
    }

    # новая
    kkk = 100 / 7 / 4
    league_distribution = {
        "Дерево": {"Дерево 1": 5.7, "Дерево 2": 5.8, "Дерево 3": 6, "Дерево 4": 7},  # 35%
        "Железо": {"Железо 1": 5, "Железо 2": 5.2, "Железо 3": 5.4, "Железо 4": 5.6},  # 30%
        "Бронза": {"Бронза 1": 4.2, "Бронза 2": 4.4, "Бронза 3": 4.6, "Бронза 4": 4.8},  # 15%
        "Серебро": {"Серебро 1": 3.4, "Серебро 2": 3.5, "Серебро 3": 3.8, "Серебро 4": 4},  # 11%
        # после Золота — обратная прогрессия (4-я подлига крупней)
        "Золото": {"Золото 4": 3.3, "Золото 3": 3, "Золото 2": 2.7, "Золото 1": 2.4},  # 6%
        "Платина": {"Платина 4": 2.2, "Платина 3": 1.9, "Платина 2": 1.6, "Платина 1": 1.3},  # 2%
        "Алмаз": {"Алмаз 4": 1.1, "Алмаз 3": 0.9, "Алмаз 2": 0.7, "Алмаз 1": 0.5},  # 1%
    }






    total_pct = sum(sum(v.values()) for v in league_distribution.values())
    if abs(total_pct - 100.0) > 1e-6:
        raise ValueError(f"Сумма долей игроков != 100, сейчас {total_pct}")

    # --- % призового пула по подлигам (сумма = 100) ---
    prize_distribution_pct = {
        "Алмаз":   {"Алмаз 1": 2.97,"Алмаз 2": 2.52,"Алмаз 3": 2.16,"Алмаз 4": 1.35},   # 9%
        "Платина": {"Платина 1": 3.63,"Платина 2": 3.08,"Платина 3": 2.64,"Платина 4": 1.65}, # 11%
        "Золото":  {"Золото 1": 6.60,"Золото 2": 5.60,"Золото 3": 4.80,"Золото 4": 3.00},    # 20%
        "Серебро": {"Серебро 1": 8.25,"Серебро 2": 7.00,"Серебро 3": 6.00,"Серебро 4": 3.75}, # 25%
        "Бронза":  {"Бронза 1": 6.60,"Бронза 2": 5.60,"Бронза 3": 4.80,"Бронза 4": 3.00},    # 20%
        "Железо":  {"Железо 1": 3.30,"Железо 2": 2.80,"Железо 3": 2.40,"Железо 4": 1.50},    # 10%
        "Дерево":  {"Дерево 1": 1.65,"Дерево 2": 1.40,"Дерево 3": 1.20,"Дерево 4": 0.75},    # 5%
    }

    # новая
    # kkk2 = 100 / 7 / 4
    fff = 1.2
    ff_ = fff / 28
    prize_distribution_pct = {
        "Алмаз": {"Алмаз 1": 5.5, "Алмаз 2": 5.35, "Алмаз 3": 5.2, "Алмаз 4": 5.05},  # 9%
        "Платина": {"Платина 1": 4.9, "Платина 2": 4.75, "Платина 3": 4.6, "Платина 4": 4.45},  # 11%
        "Золото": {"Золото 1": 4.3, "Золото 2": 4.15, "Золото 3": 4, "Золото 4": 3.85},  # 20%
        "Серебро": {"Серебро 1": 3.7, "Серебро 2": 3.55, "Серебро 3": 3.4, "Серебро 4": 3.25},  # 25%
        "Бронза": {"Бронза 1": 3.1, "Бронза 2": 2.95, "Бронза 3": 2.8, "Бронза 4": 2.65},  # 20%
        "Железо": {"Железо 1": 2.5, "Железо 2": 2.35, "Железо 3": 2.2, "Железо 4": 2.05},  # 10%
        "Дерево": {"Дерево 1": 1.9, "Дерево 2": 1.75, "Дерево 3": 1.6, "Дерево 4": 1.45},  # 5%
    }






    total_prize_pct = sum(sum(v.values()) for v in prize_distribution_pct.values())
    # print("total_prize_pct", total_prize_pct)
    # if abs(total_prize_pct - 100.0) > 1e-6:
    #     raise ValueError(f"Сумма долей приза != 100, сейчас {total_prize_pct}")

    # --- внутренние хелперы ---
    def sub_div_num(sub_name: str) -> int:
        try:
            return int(sub_name.split()[-1])
        except Exception:
            return 99

    def compute_segment_slots(dist_pct: dict, n_players: int):
        """Квоты игроков по подлигам с распределением остатков по приоритету."""
        segments = []
        for lg in league_order:
            sub = dist_pct[lg]
            for sub_name, pct in sorted(sub.items(), key=lambda kv: sub_div_num(kv[0])):  # 1..4
                exact = n_players * (pct / 100.0)
                base = int(math.floor(exact))
                rem = exact - base
                segments.append({
                    "league": lg,
                    "sub_name": sub_name,
                    "exact": exact,
                    "base": base,
                    "rem": rem,
                    "priority": (league_order.index(lg), sub_div_num(sub_name))  # меньше = сильнее
                })
        used = sum(s["base"] for s in segments)
        missing = n_players - used
        if missing > 0:
            idxs = list(range(len(segments)))
            idxs.sort(key=lambda i: (-segments[i]["rem"], segments[i]["priority"]))
            for i in idxs[:missing]:
                segments[i]["base"] += 1
        return [(s["league"], s["sub_name"], s["base"]) for s in segments]

    def assign_leagues(players_list: list, dist_pct: dict):
        """Сортируем по очкам (desc) и раскладываем по сегментам сверху вниз."""
        n = len(players_list)
        if n == 0:
            return [], []
        segments = compute_segment_slots(dist_pct, n)
        players_sorted = sorted(players_list, key=lambda p: p["point_liga"], reverse=True)

        idx = 0
        summary = []
        for league, sub_name, slots in segments:
            for _ in range(slots):
                if idx >= n:
                    break
                players_sorted[idx]["league"] = league
                players_sorted[idx]["subleague"] = sub_name  # напр. "Алмаз 1"
                idx += 1
            summary.append((league, sub_name, slots))

        while idx < n:
            players_sorted[idx]["league"] = "Дерево"
            players_sorted[idx]["subleague"] = "Дерево 4"
            idx += 1

        return players_sorted, summary

    def distribute_prizes(players_sorted: list, prize_pct: dict, alpha_val: float = 1.0):
        """В каждой подлиге делим бюджет пропорционально 1/(rank^alpha)."""
        segment_lists = defaultdict(list)
        for p in players_sorted:
            segment_lists[(p["league"], p["subleague"])].append(p)

        for (league, subleague), plist in segment_lists.items():
            # ранжируем внутри подлиги по очкам
            plist.sort(key=lambda x: x["point_liga"], reverse=True)

            seg_pct = prize_pct.get(league, {}).get(subleague, 0.0)
            seg_budget = prize_pool * (seg_pct / 100.0)
            if not plist or seg_budget <= 0:
                for p in plist:
                    p["dollar"] = 0.0
                continue

            weights = [1.0 / ((i + 1) ** alpha_val) for i in range(len(plist))]
            norm = sum(weights) if weights else 1.0
            for i, p in enumerate(plist):
                prize = seg_budget * (weights[i] / norm)
                p["dollar"] = p.get("dollar", 0.0) + prize

    # --- подготовка входа
    players = []
    for it in players_input:
        uid = it.get("user")
        pts = int(it.get("point_liga", 0) or 0)
        name = (it.get("name") or "").strip()
        players.append({"user_id": uid, "point_liga": pts, "name": name})

    # --- раскладка и призы
    players_with_leagues, _summary = assign_leagues(players, league_distribution)
    distribute_prizes(players_with_leagues, prize_distribution_pct, alpha)

    # --- группировка и ранги внутри подлиг
    per_bucket = defaultdict(list)
    for p in players_with_leagues:
        per_bucket[(p["league"], p["subleague"])].append(p)

    for key in per_bucket:
        per_bucket[key].sort(key=lambda x: x["point_liga"], reverse=True)
        for i, p in enumerate(per_bucket[key], start=1):
            p["rank_in_bucket"] = i
            p["dollar"] = round(float(p.get("dollar", 0.0)), 2)

    # --- leagues {...}
    leagues_out = {}
    for lg in league_order:
        leagues_out[lg] = {}
        for tier in (1, 2, 3, 4):
            sub_name = f"{lg} {tier}"
            plist = per_bucket.get((lg, sub_name), [])
            total_cnt = len(plist)
            top_slice = plist if top_limit_per_bucket is None else plist[:top_limit_per_bucket]
            leagues_out[lg][str(tier)] = {
                "total": total_cnt,
                "top": [
                    {
                        "user_id": p["user_id"],
                        "name": p["name"],
                        "point_liga": p["point_liga"],
                        "dollar": p["dollar"],
                        "rank": p["rank_in_bucket"]
                    }
                    for p in top_slice
                ]
            }

    # --- index {...} (включая name)
    index_out = {}
    for lg in league_order:
        for tier in ("1", "2", "3", "4"):
            for p in leagues_out[lg][tier]["top"]:
                uid = str(p["user_id"])
                if uid not in index_out or p["rank"] < index_out[uid]["rank"]:
                    index_out[uid] = {
                        "league": lg,
                        "tier": int(tier),
                        "rank": p["rank"],
                        "points": int(p["point_liga"]),
                        "dollar": float(p["dollar"]),
                        "name": p["name"],
                    }

    # добиваем индекс теми, кто не попал в top (из-за лимита)
    for (lg, sub_name), plist in per_bucket.items():
        tier_num = sub_name.split()[-1]
        for p in plist:
            uid = str(p["user_id"])
            if uid not in index_out:
                index_out[uid] = {
                    "league": lg,
                    "tier": int(tier_num),
                    "rank": p["rank_in_bucket"],
                    "points": int(p["point_liga"]),
                    "dollar": float(p["dollar"]),
                    "name": p["name"],
                }

    return {
        "meta": {
            "updated_at": int(time.time()),
            "version": 1
        },
        "index": index_out,
        "leagues": leagues_out
    }




def generate_players(num_players: int = 1000) -> list[dict]:
    """
    Генерация тестовых данных для build_top_snapshot.
    Возвращает список словарей формата:
    {"user": int, "point_liga": int, "name": str}
    """

    # Пример имён (чтобы не все были одинаковыми)
    names = [
        "Egor", "Nikolai", "Viktor", "Alex", "Maksim",
        "Anna", "Daria", "Olga", "Ivan", "Sergey",
        "Maria", "Elena", "Kirill", "Svetlana", "Roman",
        "Andrey", "Artem", "Pavel", "Oleg", "Vlad"
    ]

    players = []
    used_ids = set()

    for _ in range(num_players):
        # случайный user id (уникальный)
        uid = random.randint(100000000, 999999999)
        while uid in used_ids:
            uid = random.randint(100000000, 999999999)
        used_ids.add(uid)

        # случайное имя
        name = random.choice(names)

        # случайные очки — от 1 000 до 1 000 000, но неравномерно (чтобы были топы и слабые)
        point_liga = int(random.expovariate(1 / 200000))  # смещённое распределение
        point_liga = min(max(point_liga, 1000), 1_000_000)

        players.append({
            "user": uid,
            "point_liga": point_liga,
            "name": name
        })

    return players



def print_top_snapshot(snapshot: dict):
    """
    Печатает только ТОП-5 игроков в каждой подлиге.
    Формат: <Лига> <Номер> | <Имя> | <Очки> | <Доллары>
    """
    league_order = ["Алмаз", "Платина", "Золото", "Серебро", "Бронза", "Железо", "Дерево"]
    leagues = snapshot.get("leagues", {})

    for lg in league_order:
        lg_data = leagues.get(lg, {})
        for tier in ("1", "2", "3", "4"):
            sub = lg_data.get(tier, {})
            players = sub.get("top", [])
            total = sub.get("total", 0)
            if not players:
                continue

            print(f"\n===== {lg} {tier} ===== (всего игроков: {total})")

            for p in players[:5]:
                name = p["name"]
                pts = p["point_liga"]
                dol = p["dollar"]
                print(f"{lg} {tier} | {name:<15} | {pts:>8} очков | ${dol:>6.2f}")



# plr = generate_players(3000)
#
# ff = build_top_snapshot(plr, prize_pool=3000)
# print_top_snapshot(ff)



