# pip install rich
import random
import math
import csv
from pathlib import Path
from collections import defaultdict

from rich.console import Console
from rich.table import Table
from rich import box

# ===== ПАРАМЕТРЫ =====
PLAYERS_COUNT = 3
PRIZE_POOL = 3_000   # общий призовой фонд, $
ALPHA = 1.0              # "резкость" распределения призов внутри подлиги (1.0 = 1/место)
TOP_LIMIT = None         # None = печатать всех; или, например, 200
OUTPUT_CSV = Path("top_players.csv")  # путь к файлу для выгрузки топа

console = Console()

# ===== Генерация игроков (уникальные очки, больше = сильнее) =====
points = random.sample(range(1, 100_000), PLAYERS_COUNT)
players = [{"user": f"user_{i}", "point": pt} for i, pt in enumerate(points, start=1)]


# ===== Доли игроков по лигам/подлигам (в процентах, сумма = 100.0) =====
league_distribution = {
    "Дерево": {"Дерево 1": 16.0, "Дерево 2": 9.0, "Дерево 3": 6.0, "Дерево 4": 4.0},         # 35%
    "Железо": {"Железо 1": 14.0, "Железо 2": 8.0, "Железо 3": 5.0, "Железо 4": 3.0},        # 30%
    "Бронза": {"Бронза 1": 8.0, "Бронза 2": 4.0, "Бронза 3": 2.0, "Бронза 4": 1.0},         # 15%
    "Серебро": {"Серебро 1": 5.0, "Серебро 2": 3.0, "Серебро 3": 2.0, "Серебро 4": 1.0},    # 11%
    # после Золота — обратная прогрессия (4-я подлига крупней)
    "Золото": {"Золото 4": 3.0, "Золото 3": 1.5, "Золото 2": 1.0, "Золото 1": 0.5},        # 6%
    "Платина": {"Платина 4": 1.0, "Платина 3": 0.5, "Платина 2": 0.35, "Платина 1": 0.15},  # 2%
    "Алмаз": {"Алмаз 4": 0.5, "Алмаз 3": 0.3, "Алмаз 2": 0.15, "Алмаз 1": 0.05},            # 1%
}
total_pct = sum(sum(v.values()) for v in league_distribution.values())
assert abs(total_pct - 100.0) < 1e-9, f"Сумма долей игроков != 100, сейчас {total_pct}"

# ===== Процентная раскладка призового фонда по подлигам (сумма = 100.00%) =====
prize_distribution_pct = {
    "Алмаз": {
        "Алмаз 1": 2.97,
        "Алмаз 2": 2.52,
        "Алмаз 3": 2.16,
        "Алмаз 4": 1.35,
    },  # итого 9%

    "Платина": {
        "Платина 1": 3.63,
        "Платина 2": 3.08,
        "Платина 3": 2.64,
        "Платина 4": 1.65,
    },  # итого 11%

    "Золото": {
        "Золото 1": 6.60,
        "Золото 2": 5.60,
        "Золото 3": 4.80,
        "Золото 4": 3.00,
    },  # итого 20%

    "Серебро": {
        "Серебро 1": 8.25,
        "Серебро 2": 7.00,
        "Серебро 3": 6.00,
        "Серебро 4": 3.75,
    },  # итого 25%

    "Бронза": {
        "Бронза 1": 6.60,
        "Бронза 2": 5.60,
        "Бронза 3": 4.80,
        "Бронза 4": 3.00,
    },  # итого 20%

    "Железо": {
        "Железо 1": 3.30,
        "Железо 2": 2.80,
        "Железо 3": 2.40,
        "Железо 4": 1.50,
    },  # итого 10%

    "Дерево": {
        "Дерево 1": 1.65,
        "Дерево 2": 1.40,
        "Дерево 3": 1.20,
        "Дерево 4": 0.75,
    },  # итого 5%
}


total_prize_pct = sum(sum(v.values()) for v in prize_distribution_pct.values())
assert abs(total_prize_pct - 100.0) < 1e-9, f"Сумма долей приза != 100, сейчас {total_prize_pct}"

# ===== Порядок силы лиг и подлиг =====
league_order = ["Алмаз", "Платина", "Золото", "Серебро", "Бронза", "Железо", "Дерево"]

def sub_div_num(sub_name: str) -> int:
    """Номер подлиги (1..4), где 1 — сильнейшая."""
    try:
        return int(sub_name.split()[-1])
    except Exception:
        return 99

# ===== Квоты игроков на сегменты (лига+подлига) по % распределению =====
def compute_segment_slots(dist_pct: dict, n_players: int):
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

# ===== Присвоение лиг игрокам по очкам =====
def assign_leagues(players_list: list, dist_pct: dict):
    n = len(players_list)
    segments = compute_segment_slots(dist_pct, n)
    players_sorted = sorted(players_list, key=lambda p: p["point"], reverse=True)

    idx = 0
    summary = []
    for league, sub_name, slots in segments:
        for _ in range(slots):
            if idx >= n:
                break
            players_sorted[idx]["league"] = league
            players_sorted[idx]["subleague"] = sub_name
            idx += 1
        summary.append((league, sub_name, slots))

    # На всякий случай (не должно случиться)
    while idx < n:
        players_sorted[idx]["league"] = "Дерево"
        players_sorted[idx]["subleague"] = "Дерево 4"
        idx += 1

    return players_sorted, summary

# ===== Распределение призов внутри каждой подлиги по обратной пропорции к месту =====
def distribute_prizes(players_sorted: list, prize_pct: dict, alpha: float = 1.0):
    """
    Бюджет подлиги = PRIZE_POOL * prize_pct/100.
    Внутри подлиги: weight_i = 1 / (rank_in_subleague ** alpha).
    """
    segment_lists = defaultdict(list)
    for p in players_sorted:
        segment_lists[(p["league"], p["subleague"])].append(p)

    total_paid = 0.0
    for (league, subleague), plist in segment_lists.items():
        seg_pct = prize_pct.get(league, {}).get(subleague, 0.0)
        seg_budget = PRIZE_POOL * (seg_pct / 100.0)

        # Веса по местам в ПОДЛИГЕ (ранг 1..N внутри конкретной подлиги)
        weights = [1.0 / ((i + 1) ** alpha) for i in range(len(plist))]
        norm = sum(weights) if weights else 1.0
        for i, p in enumerate(plist):
            prize = seg_budget * (weights[i] / norm)
            p["prize"] = p.get("prize", 0.0) + prize
            total_paid += prize
    return total_paid

def extract_sub_num(subleague: str) -> str:
    try:
        return str(int(subleague.split()[-1]))
    except Exception:
        return "?"

# ===== Красивые таблицы через Rich =====
def print_segment_budgets_table(prize_pct: dict):
    """Таблица бюджетов подлиг (в $ и %)."""
    table = Table(title="Бюджеты подлиг (из призового фонда)", box=box.SIMPLE_HEAVY)
    table.add_column("Название лиги", style="bold cyan")
    table.add_column("Номер лиги", justify="right")
    table.add_column("% пула", justify="right")
    table.add_column("Бюджет, $", justify="right")

    for lg in league_order:
        for sub_name, pct in sorted(prize_pct[lg].items(), key=lambda kv: sub_div_num(kv[0])):
            amount = PRIZE_POOL * pct / 100.0
            table.add_row(lg, sub_name.split()[-1], f"{pct:.2f}", f"{amount:,.2f}")
    console.print(table)

def print_full_top_rich(players_list: list, limit: int | None = None):
    """
    Печатает топ (все или первые limit) в формате:
    Название лиги | Номер лиги | Место в лиге | Имя игрока | Очки | Выигрыш, $
    Место считается отдельно в каждой подлиге.
    """
    players_sorted = sorted(players_list, key=lambda x: x["point"], reverse=True)
    rank_in_subleague = defaultdict(int)

    table = Table(title="Топ игроков", box=box.MINIMAL_DOUBLE_HEAD, row_styles=["none", "dim"])
    table.add_column("Название лиги", style="cyan")
    table.add_column("Номер лиги", justify="right")
    table.add_column("Место в лиге", justify="right")
    table.add_column("Имя игрока", style="bold")
    table.add_column("Очки", justify="right")
    table.add_column("Выигрыш, $", justify="right", style="green")

    rows_printed = 0
    for p in players_sorted:
        league = p.get("league", "?")
        subleague = p.get("subleague", "?")
        key = (league, subleague)
        rank_in_subleague[key] += 1  # место в своей подлиге
        place_in_subleague = rank_in_subleague[key]

        sub_num = extract_sub_num(subleague)
        prize_str = f"{p.get('prize', 0.0):.2f}"

        table.add_row(league, sub_num, str(place_in_subleague), p["user"], f"{p['point']}", prize_str)
        rows_printed += 1
        if limit is not None and rows_printed >= limit:
            break

    console.print(table)

# ===== Экспорт полного топа в CSV =====
def export_full_top_csv(players_list: list, path: Path):
    """
    Выгружает весь топ в CSV с колонками:
    Название лиги, Номер лиги, Место в лиге, Имя игрока, Очки, Выигрыш, $
    """
    players_sorted = sorted(players_list, key=lambda x: x["point"], reverse=True)
    rank_in_subleague = defaultdict(int)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=",")
        writer.writerow(["Название лиги", "Номер лиги", "Место в лиге", "Имя игрока", "Очки", "Выигрыш, $"])
        for p in players_sorted:
            league = p.get("league", "?")
            subleague = p.get("subleague", "?")
            key = (league, subleague)
            rank_in_subleague[key] += 1
            place_in_subleague = rank_in_subleague[key]

            sub_num = extract_sub_num(subleague)
            prize_val = p.get("prize", 0.0)
            writer.writerow([league, sub_num, place_in_subleague, p["user"], p["point"], f"{prize_val:.2f}"])

    console.print(f"[bold green]CSV сохранён:[/bold green] {path.resolve()}")


# ===== Запуск =====
players_with_leagues, summary = assign_leagues(players, league_distribution)
total_paid = distribute_prizes(players_with_leagues, prize_distribution_pct, alpha=ALPHA)

# Таблица бюджетов подлиг (для наглядности в терминале)
print_segment_budgets_table(prize_distribution_pct)

# Печатаем топ в терминале (или первые TOP_LIMIT строк)
print_full_top_rich(players_with_leagues, limit=TOP_LIMIT)

# Экспортируем полный топ в CSV
export_full_top_csv(players_with_leagues, OUTPUT_CSV)

# ===== Проверка: сходятся ли деньги =====
calc_sum = sum(p.get("prize", 0.0) for p in players_with_leagues)
check_table = Table(title="Проверка суммы призов", box=box.SIMPLE_HEAVY)
check_table.add_column("Параметр", style="bold")
check_table.add_column("Значение", justify="right")
check_table.add_row("Ожидалось к выплате", f"{PRIZE_POOL:,.2f} $")
check_table.add_row("Начислено суммарно", f"{calc_sum:,.6f} $")
check_table.add_row("Погрешность", f"{abs(calc_sum - PRIZE_POOL):,.6f} $")
console.print(check_table)
