import json
import math
import random
import secrets
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any

ROWS = 11
MULTIPLIERS = [15, 7, 4, 2, 1.1, 0.5, 0.3, 0.5, 1.1, 2, 4, 7, 15]
# MULTIPLIERS = [15.6, 7.5, 3.7, 2.2, 1.1, 0.6, 0.16, 0.6, 1.1, 2.2, 3.7, 7.5, 15.6]
BALL_RADIUS = 9
PIN_RADIUS = 7
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 800

GRAVITY = 0.6
FRICTION = 0.95
BOUNCE = 0.66

TIME_STEP = 0.06  # шаг интеграции (сек.)

@dataclass
class Frame:
    t: float
    x: float
    y: float
    vx: float
    vy: float

@dataclass
class Collision:
    index: int
    time: float
    pin_x: float
    pin_y: float
    exit_vx: float
    exit_vy: float

def seed_rng(seed: Optional[str]) -> Tuple[random.Random, str]:
    """Возвращает seeded RNG и сам seed."""
    if seed:
        rng = random.Random(seed)
        return rng, seed
    seed = secrets.token_hex(16)
    rng = random.Random(seed)
    return rng, seed

def build_pin_grid() -> List[Dict[str, float]]:
    """Выстраиваем пины (точно как на фронте)."""
    pins = []
    max_pins_per_row = ROWS + 1  # последний ряд (11-й) = 12 пинов
    spacing_x = DISPLAY_WIDTH / (max_pins_per_row + 1)
    spacing_y = (DISPLAY_HEIGHT * 0.75) / ROWS
    start_y = DISPLAY_HEIGHT * 0.08
    for row in range(ROWS):
        pins_in_row = row + 2
        start_x = (DISPLAY_WIDTH - (pins_in_row - 1) * spacing_x) / 2
        for col in range(pins_in_row):
            pins.append({
                "x": start_x + col * spacing_x,
                "y": start_y + row * spacing_y
            })
    return pins

def slot_geometry(pin_list) -> Dict[str, Any]:
    """Геометрия слотов (центры, ширины) — идентично фронту."""
    slots_count = len(MULTIPLIERS)
    last_row_start = sum(range(2, ROWS + 2)) - (ROWS + 1)
    last_row = pin_list[last_row_start:]
    pins_to_use = last_row[1:slots_count + 1]
    if len(pins_to_use) > 1:
        avg_spacing = sum(
            pins_to_use[i + 1]["x"] - pins_to_use[i]["x"]
            for i in range(len(pins_to_use) - 1)
        ) / (len(pins_to_use) - 1)
    else:
        avg_spacing = DISPLAY_WIDTH / (slots_count + 1)
    slot_width = avg_spacing * 0.9
    total_slots_width = (slots_count - 1) * avg_spacing + slot_width
    slots_start_x = (DISPLAY_WIDTH - total_slots_width) / 2
    centers = [slots_start_x + slot_width / 2 + i * avg_spacing
               for i in range(slots_count)]
    return {
        "slot_height": 55,
        "slot_y": DISPLAY_HEIGHT - 55 - 10,
        "slot_width": slot_width,
        "avg_spacing": avg_spacing,
        "slots_start_x": slots_start_x,
        "centers": centers
    }

def generate_plinko_scenario(bet: float, seed: Optional[str] = None) -> Dict[str, Any]:
    """Основной генератор, отдаёт JSON-структуру для фронта."""
    if bet <= 0:
        raise ValueError("Bet must be positive")

    rng, seed = seed_rng(seed)
    pins = build_pin_grid()
    geometry = slot_geometry(pins)
    slot_y = geometry["slot_y"]
    slot_height = geometry["slot_height"]
    slot_floor = slot_y + slot_height

    start_x = DISPLAY_WIDTH / 2 + (rng.random() - 0.5) * 26
    start_y = 20.0
    vx = (rng.random() - 0.5) * 2
    vy = 0.0

    ball = {"x": start_x, "y": start_y, "vx": vx, "vy": vy}
    frames: List[Frame] = []
    collisions: List[Collision] = []
    t = 0.0

    def push_frame():
        frames.append(Frame(
            t=round(t, 3),
            x=round(ball["x"], 2),
            y=round(ball["y"], 2),
            vx=round(ball["vx"], 2),
            vy=round(ball["vy"], 2)
        ))

    push_frame()

    while True:
        prev_x = ball["x"]
        prev_y = ball["y"]
        prev_vx = ball["vx"]
        prev_vy = ball["vy"]
        prev_t = t

        ball["vy"] += GRAVITY
        ball["x"] += ball["vx"]
        ball["y"] += ball["vy"]

        for pin in pins:
            dx = ball["x"] - pin["x"]
            dy = ball["y"] - pin["y"]
            distance = math.hypot(dx, dy)
            if distance < BALL_RADIUS + PIN_RADIUS:
                angle = math.atan2(dy, dx)
                speed = math.hypot(ball["vx"], ball["vy"])
                random_factor = rng.uniform(0.9, 1.1)
                ball["vx"] = math.cos(angle) * speed * BOUNCE * random_factor
                ball["vy"] = math.sin(angle) * speed * BOUNCE * random_factor
                overlap = BALL_RADIUS + PIN_RADIUS - distance + 1
                ball["x"] += math.cos(angle) * overlap
                ball["y"] += math.sin(angle) * overlap
                collisions.append(Collision(
                    index=len(collisions) + 1,
                    time=round(prev_t, 3),
                    pin_x=round(pin["x"], 1),
                    pin_y=round(pin["y"], 1),
                    exit_vx=round(ball["vx"], 2),
                    exit_vy=round(ball["vy"], 2)
                ))
                break

        if ball["x"] - BALL_RADIUS < 0 or ball["x"] + BALL_RADIUS > DISPLAY_WIDTH:
            ball["vx"] *= -BOUNCE
            ball["x"] = max(BALL_RADIUS, min(DISPLAY_WIDTH - BALL_RADIUS, ball["x"]))
        ball["vx"] *= FRICTION

        t += TIME_STEP

        crossed_floor = prev_y <= slot_floor and ball["y"] > slot_floor
        if crossed_floor:
            denom = ball["y"] - prev_y
            ratio = 1.0 if abs(denom) < 1e-6 else max(0.0, min(1.0, (slot_floor - prev_y) / denom))
            cross_t = prev_t + TIME_STEP * ratio
            cross_x = prev_x + (ball["x"] - prev_x) * ratio
            cross_vx = prev_vx + (ball["vx"] - prev_vx) * ratio
            cross_vy = prev_vy + (ball["vy"] - prev_vy) * ratio

            ball["x"] = cross_x
            ball["y"] = slot_floor
            ball["vx"] = cross_vx
            ball["vy"] = cross_vy
            t = cross_t

            frames.append(Frame(
                t=round(cross_t, 3),
                x=round(ball["x"], 2),
                y=round(ball["y"], 2),
                vx=round(ball["vx"], 2),
                vy=round(ball["vy"], 2)
            ))
            break

        push_frame()

        if ball["y"] > slot_floor:
            ball["y"] = slot_floor
            frames.append(Frame(
                t=round(t, 3),
                x=round(ball["x"], 2),
                y=round(ball["y"], 2),
                vx=round(ball["vx"], 2),
                vy=round(ball["vy"], 2)
            ))
            break

        if t > 30:
            break

    if frames:
        last_frame = frames[-1]
        target_y = round(slot_floor, 2)
        if last_frame.y < target_y:
            settle_t = round(last_frame.t + TIME_STEP / 4, 3)
            frames.append(Frame(
                t=settle_t,
                x=last_frame.x,
                y=target_y,
                vx=0.0,
                vy=max(0.0, last_frame.vy)
            ))
            ball["x"] = last_frame.x
            ball["y"] = slot_floor

    slot_index = -1
    slot_center_x = None
    for i, center in enumerate(geometry["centers"]):
        left = center - geometry["slot_width"] / 2
        right = center + geometry["slot_width"] / 2
        if left <= ball["x"] <= right:
            slot_index = i
            slot_center_x = center
            break

    if slot_index == -1:
        distances = [abs(ball["x"] - center) for center in geometry["centers"]]
        slot_index = distances.index(min(distances))
        slot_center_x = geometry["centers"][slot_index]

    multiplier = MULTIPLIERS[slot_index]
    win_amount = round(bet * multiplier, 2)

    scenario = {
        "meta": {
            "seed": seed,
            "rows": ROWS,
            "multiplier_list": MULTIPLIERS,
            "plan_type": "frames"
        },
        "ball": {
            "radius": BALL_RADIUS,
            "color": "#ff7f00",
            "start_x": round(start_x, 2),
            "start_y": start_y,
            "start_vx": round(vx, 2),
            "start_vy": round(vy, 2)
        },
        "result": {
            "slot_index": slot_index,
            "multiplier": multiplier,
            "bet": round(bet, 2),
            "win_amount": win_amount
        },
        "frames": [asdict(f) for f in frames],
        "collisions": [asdict(c) for c in collisions],
        "slot_hit": {
            "time": frames[-1].t,
            "slot_center_x": round(slot_center_x or geometry["centers"][0], 2),
            "slot_center_y": round(geometry["slot_y"] + geometry["slot_height"] / 2, 2)
        },
        "effects": {
            "particles_seed": rng.randint(0, 2**31 - 1),
            "coins_seed": rng.randint(0, 2**31 - 1)
        }
    }

    last_frame = frames[-1] if frames else None
    have_touch = (
        last_frame is not None
        and abs(last_frame.y - slot_floor) <= 1e-2
        and 0 <= slot_index < len(MULTIPLIERS)
    )

    if not have_touch:
        # перегенерация с новым seed
        new_seed = secrets.token_hex(16)
        return generate_plinko_scenario(bet, new_seed)

    return scenario


def start_data():
    return {
        "ROWS": ROWS,
        "MULTIPLIERS": MULTIPLIERS,
        "BALL_RADIUS": BALL_RADIUS,
        "PIN_RADIUS": PIN_RADIUS,
        "DISPLAY_WIDTH": DISPLAY_WIDTH,
        "DISPLAY_HEIGHT": DISPLAY_HEIGHT,
        "GRAVITY": GRAVITY,
        "FRICTION": FRICTION,
        "BOUNCE": BOUNCE
    }