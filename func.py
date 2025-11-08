from collections import defaultdict
from typing import Dict, Any, Optional, List
import random

# определение стилья подарка и силы
import settings



def hype_phrase(score: int) -> str:
    s = str(score)
    s_spaced = f"{score:,}".replace(",", " ")  # 53000 -> "53 000"
    templates = [
        "<b>Выиграл!</b>\nВау, чувак, это реально круто! Ты набрал {s_spaced} очков и уделал противника!",
        "<b>Выиграл!</b>\nКрасавчик! {s_spaced} и победа твоя! Где ты так прокачал пальцы?",
        "<b>Выиграл!</b>\nСколько-сколько? {s_spaced} очков?! Победа твоя, респект!",
        "<b>Выиграл!</b>\nТы победил! {s_spaced} очков! От души душевно в душу братишка!",
        "<b>Выиграл!</b>\nОууу, вот это перфоманс! {s_spaced} очков и уверенная победа. Дай пять, чемпион! 🖐",
        "<b>Выиграл!</b>\nПепе гордится тобой. {s_spaced} очков — и ты снова в топе!",
        "<b>Выиграл!</b>\nЭто было чеертовски красиво! {s_spaced} очков, и враг повержен. Танцуй, герой! 💃",
    ]
    return random.choice(templates).format(s=s, s_spaced=s_spaced)


def lose_phrase(score: int) -> str:
    s = str(score)
    s_spaced = f"{score:,}".replace(",", " ")  # 12000 → "12 000"
    templates = [
        "<b>Проиграл</b>\nНу… бывает. Не расстраивайся, может твой друг еще отомстит за тебя 💪",
        f"<b>Проиграл</b>\n-{s_spaced} очков? Да ты почти победил… если бы противник играл одной рукой 😅",
        "<b>Проиграл</b>\nНе твой ритм, брат. Но пальцы уже прогрел — следующая победа за тобой!",
        "<b>Проиграл</b>\nПепе расстроен, но верит в камбэк. Скажи врагу напоследок — I WILL BE BACK 💀",
        f"<b>Проиграл</b>\nЧто ж, ты же не сдашься, да? -{s_spaced} очков маловато, так что возвращайся в игру и отомсти!",
    ]
    return random.choice(templates)


def get_damage_bonus(item_name: str) -> str:
    value = settings.super_gift.get(item_name)
    if value is None:
        return 0

    if value < 1000:
        bonus = 18
    elif value < 5000:
        bonus = 15
    elif value < 10000:
        bonus = 12
    elif value < 15000:
        bonus = 9
    elif value < 20000:
        bonus = 6
    elif value < 30000:
        bonus = 3
    elif value < 40000:
        bonus = 2
    else:
        bonus = 0

    return bonus


def power_chek(data):

    def fefe(point):
        power = 0
        for i in point:
            if i <= 0.5:
                power0 = 10
            elif i <= 1:
                power0 = 8
            elif i <= 1.5:
                power0 = 6
            else:
                power0 = 4

            power += power0

        dd = {
            "power": power,
            "style": ""
        }
        return dd

    li = []

    # список для поиска минимального rarity
    rarity_list = []

    for i in data:
        # print(i)

        try:
            if i["rarity"] == None:
                continue
            rarity_val = i["rarity"] / 10
            li.append(rarity_val)
        except:
            # print(data)
            print("не ок", i)
            pass

        # print("ok", i)
        # сохраняем (rarity, type)
        rarity_list.append((i["rarity"], i["type"]))

    dd = fefe(li)

    # ищем минимальный rarity
    min_attr = min(rarity_list, key=lambda x: x[0])
    attr_type = min_attr[1].replace("GiftAttributeType.", "")



    return dd



def get_strongest_style(
    gear: Dict[str, Any],
    *,
    allowed: Optional[List[str]] = None,
    priority: Optional[List[str]] = None,
    default: Optional[str] = None,
) -> Optional[str]:
    """
    Суммирует power по стилям ("beat", "style", "rhythm") и возвращает стиль с максимальной суммой.

    - allowed: список разрешённых стилей; если None — берём все.
    - priority: список стилей по приоритету при ничьей; если None — алфавит.
    - default: что вернуть, если данных нет.
    """
    if allowed is None:
        allowed = ["beat", "style", "rhythm"]
    if priority is None:
        priority = allowed  # используем тот же порядок как приоритет

    totals = defaultdict(int)

    if not isinstance(gear, dict):
        return default

    for item in gear.values():
        if not isinstance(item, dict) or not item:
            continue
        style = item.get("style")
        power = item.get("power")
        if style not in allowed or not isinstance(power, (int, float)):
            continue
        totals[style] += int(power)

    if not totals:
        return default

    max_sum = max(totals.values())
    winners = [s for s, v in totals.items() if v == max_sum]

    if len(winners) == 1:
        return winners[0]

    for s in priority:  # выбираем первый по приоритету
        if s in winners:
            return s

    return sorted(winners)[0]  # запасной вариант

def pick_nearby_rival(data: dict, id_telega: int, window: int = 10):
    """
    1) Пытается выбрать случайного соперника с ненулевыми очками из лиг в окне +-window позиций.
    2) Если игрок id_telega не найден ИЛИ кандидатов нет — возвращает ID игрока с минимальным положительным point_liga во всех топах.
    3) Если вообще нет ни одного игрока с point_liga > 0 — вернёт None.
    """

    order = [
        'tree_4','tree_3','tree_2','tree_1',
        'iron_4','iron_3','iron_2','iron_1',
        'bronze_4','bronze_3','bronze_2','bronze_1',
        'silver_4','silver_3','silver_2','silver_1',
        'gold_4','gold_3','gold_2','gold_1',
        'platinum_4','platinum_3','platinum_2','platinum_1',
        'diamond_4','diamond_3','diamond_2','diamond_1'
    ]
    order_index = {g: i for i, g in enumerate(order)}

    ru2code = {
        'Дерево': 'tree',
        'Железо': 'iron',
        'Бронза': 'bronze',
        'Серебро': 'silver',
        'Золото': 'gold',
        'Платина': 'platinum',
        'Алмаз': 'diamond',
    }

    def global_lowest(exclude_id: int | None = None):
        """Самый 'низкий' по point_liga > 0 во всех лигах (минимум)."""
        leagues = data.get('leagues', {})
        min_point = None
        min_user_id = None
        for league_data in leagues.values():
            for tier_data in league_data.values():
                for entry in tier_data.get('top', []):
                    uid = entry.get('user_id')
                    if exclude_id is not None and str(uid) == str(exclude_id):
                        continue
                    p = entry.get('point_liga', 0)
                    if isinstance(p, (int, float)) and p > 0:
                        if min_point is None or p < min_point:
                            min_point = p
                            min_user_id = uid
        return min_user_id

    idx = data.get('index', {}) or {}

    # Если игрок отсутствует — сразу фолбэк
    me = idx.get(str(id_telega)) or idx.get(id_telega)
    if not me:
        return global_lowest(exclude_id=None)

    # Определяем позицию игрока на шкале
    league_ru = me.get('league')
    tier = me.get('tier')
    if league_ru not in ru2code or not isinstance(tier, int):
        return global_lowest(exclude_id=id_telega)

    my_grade = f"{ru2code[league_ru]}_{tier}"
    if my_grade not in order_index:
        return global_lowest(exclude_id=id_telega)

    my_pos = order_index[my_grade]
    lo = max(0, my_pos - window)
    hi = min(len(order) - 1, my_pos + window)

    # Функция для позиции лиги игрока
    def grade_pos(entry):
        lg_ru = entry.get('league')
        tr = entry.get('tier')
        if lg_ru not in ru2code or not isinstance(tr, int):
            return None
        g = f"{ru2code[lg_ru]}_{tr}"
        return order_index.get(g)

    # Сбор кандидатов (не сам игрок, в окне, очки > 0)
    candidates = []
    for uid, info in idx.items():
        if str(uid) == str(id_telega):
            continue
        pos = grade_pos(info)
        if pos is None or pos < lo or pos > hi:
            continue
        # допускаем points (из index) и point_liga (если встретится)
        points = info.get('points', 0)
        if not isinstance(points, (int, float)):
            points = 0
        point_liga = info.get('point_liga', 0)
        if not isinstance(point_liga, (int, float)):
            point_liga = 0
        if (points > 0) or (point_liga > 0):
            candidates.append(int(uid))

    if candidates:
        return random.choice(candidates)

    # Фолбэк: глобально минимальный point_liga > 0 (исключая самого игрока)
    return global_lowest(exclude_id=id_telega)

