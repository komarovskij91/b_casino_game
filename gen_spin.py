import json
import random
import secrets
from typing import Dict, List, Optional, Tuple

ROWS = 11
MULTIPLIERS = [8, 5, 3, 1.5, 0.8, 0.6, 0.4, 0.6, 0.8, 1.5, 3, 5, 8]

def seed_rng(seed: Optional[str]) -> Tuple[random.Random, str]:
    if seed:
        rng = random.Random(seed)
        return rng, seed
    seed = secrets.token_hex(16)
    rng = random.Random(seed)
    return rng, seed

def generate_plinko_path(bet: float, seed: Optional[str] = None) -> Dict[str, object]:
    """
    Генерирует сценарий для «path-based» фронта:
      - start_index начинается из центра (как в игре)
      - на каждом ряду выдаётся move: -1 (влево), 0 (прямо) или 1 (вправо)
      - фронт использует path, чтобы воспроизвести движение с реальной физикой
    """
    if bet <= 0:
        raise ValueError("Bet must be positive")

    rng, seed = seed_rng(seed)

    # середина треугольника в текущей схеме (13 слотов -> индекс 6)
    position = (len(MULTIPLIERS) - 1) / 2
    moves: List[int] = []

    for row in range(ROWS - 1):
        move = rng.choice([-1, 0, 1])

        # Не даём выйти за диапазон
        if position <= 0 and move < 0:
            move = rng.choice([0, 1])
        if position >= len(MULTIPLIERS) - 1 and move > 0:
            move = rng.choice([-1, 0])

        moves.append(move)
        position += move

        # Чуть «прижимаем» к диапазону, чтобы не набегать на границы
        position = max(0, min(position, len(MULTIPLIERS) - 1))

    slot_index = int(round(position))
    slot_index = max(0, min(slot_index, len(MULTIPLIERS) - 1))

    multiplier = MULTIPLIERS[slot_index]
    win_amount = round(bet * multiplier, 2)

    scenario = {
        "meta": {
            "seed": seed,
            "rows": ROWS,
            "multiplier_list": MULTIPLIERS,
            "plan_type": "path"
        },
        "ball": {
            "radius": 8,
            "color": "#ff7f00",
            "start_x": 400.0,   # фронт всё равно ставит шарик в центр; можно не использовать
            "start_y": 20.0
        },
        "result": {
            "slot_index": slot_index,
            "multiplier": multiplier,
            "bet": round(bet, 2),
            "win_amount": win_amount
        },
        "path": moves,
        "effects": {
            "particles_seed": rng.randint(0, 2**31 - 1),
            "coins_seed": rng.randint(0, 2**31 - 1)
        }
    }
    return scenario



# dd = generate_plinko_path(10)
# print(dd)