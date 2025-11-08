



new_user = {
    "id_telega": None,

    "first_name": None,
    "last_name": None,
    "lang": 'en',
    "photo_url": "",

    "prem": None,
    "username": None,

    # проверка дней
    "day": 0,
    "day_time": 0,

    "name": "",
    "data_reg": "",
    "ref": "",
    "ref_bonus": False,
    "old_time": 0,  # последний раз заходил
    "old_day": 0,
    "old_time_reg_energ": 0,  # последний раз реген енерг

    # Очки лиги
    "point_liga": 0,  # тут копятся очки снежинки
    "count_player": 0,

    "list_gift": [],

    # ads
    "all_ads": 0,
    "day_ads": 0,  # реклам просмотрено за день

    # для чека иголок
    "old_time_click": 0,

    # баланс звезд
    "stars": 0,
    "snowman": False,


    # реф
    "ref_ok": 0,

    "slot_1": {
        "status": "open",
        "slot": None,
        "color": "",
        "proc": 0
    },
    "slot_2": {
        "status": "open",
        "slot": None,
        "color": "",
        "proc": 0
    },
    "slot_3": {
        "status": "open",
        "slot": None,
        "color": "",
        "proc": 0
    },
    "slot_4": {
        "status": "close",
        "slot": None,
        "color": "",
        "proc": 0
    },
    "slot_5": {
        "status": "close",
        "slot": None,
        "color": "",
        "proc": 0
    },
    "slot_6": {
        "status": "close",
        "slot": None,
        "color": "",
        "proc": 0
    },
    "slot_7": {
        "status": "close",
        "slot": None,
        "color": "",
        "proc": 0
    },
    "slot_8": {
        "status": "close",
        "slot": None,
        "color": "",
        "proc": 0
    }


}





test_spin = {
  "meta": {
    "seed": "0f9b2e03-2a0a-4d08-8bb9-3bbba32d95fd",
    "rows": 11,
    "multiplier_list": [8, 5, 3, 1.5, 0.8, 0.6, 0.4, 0.6, 0.8, 1.5, 3, 5, 8]
  },
  "ball": {
    "radius": 8,
    "color": "#ff7f00",
    "start_x": 402.40,
    "start_y": 20.00,
    "start_vx": -0.20,
    "start_vy": 0.00
  },
  "result": {
    "slot_index": 4,
    "multiplier": 0.8,
    "bet": 10.0,
    "win_amount": 8.0
  },
  "path": [-1, 0, 1, 0, -1, -1, 0, 1, 0, -1],
  "frames": [
    {"t":0.00,"x":402.40,"y":20.00,"vx":-0.20,"vy":0.00},
    {"t":0.10,"x":401.98,"y":42.30,"vx":-0.32,"vy":2.23},
    {"t":0.20,"x":401.31,"y":68.42,"vx":-0.46,"vy":4.52},
    {"t":0.30,"x":400.38,"y":98.38,"vx":-0.63,"vy":6.80},
    {"t":0.40,"x":398.69,"y":133.62,"vx":-1.13,"vy":7.45},
    {"t":0.50,"x":396.40,"y":172.24,"vx":-1.11,"vy":7.82},
    {"t":0.60,"x":394.02,"y":212.03,"vx":-1.08,"vy":7.93},
    {"t":0.70,"x":391.46,"y":251.90,"vx":-1.04,"vy":8.16},
    {"t":0.80,"x":388.92,"y":291.76,"vx":-1.00,"vy":8.21},
    {"t":0.90,"x":386.36,"y":331.59,"vx":-0.95,"vy":8.16},
    {"t":1.00,"x":387.00,"y":371.50,"vx":1.24,"vy":7.90},
    {"t":1.10,"x":389.42,"y":410.41,"vx":1.34,"vy":7.88},
    {"t":1.20,"x":391.78,"y":449.42,"vx":1.26,"vy":8.22},
    {"t":1.30,"x":394.07,"y":488.53,"vx":1.12,"vy":8.35},
    {"t":1.40,"x":393.21,"y":527.53,"vx":-1.16,"vy":8.34},
    {"t":1.50,"x":390.95,"y":566.47,"vx":-1.39,"vy":8.68},
    {"t":1.60,"x":388.67,"y":605.37,"vx":-1.25,"vy":8.96},
    {"t":1.70,"x":386.40,"y":644.23,"vx":-1.16,"vy":8.95},
    {"t":1.80,"x":384.13,"y":683.04,"vx":-1.07,"vy":9.01},
    {"t":1.90,"x":381.84,"y":721.79,"vx":-1.02,"vy":8.96},
    {"t":2.00,"x":381.03,"y":746.21,"vx":-0.82,"vy":5.00},
    {"t":2.10,"x":380.70,"y":767.65,"vx":-0.44,"vy":3.41},
    {"t":2.20,"x":380.61,"y":784.94,"vx":-0.17,"vy":2.15},
    {"t":2.30,"x":380.58,"y":799.30,"vx":-0.04,"vy":1.20},
    {"t":2.40,"x":380.57,"y":810.05,"vx":-0.01,"vy":0.52},
    {"t":2.50,"x":380.57,"y":817.20,"vx":-0.00,"vy":0.06}
  ],
  "collisions": [
    {"index":1,"time":0.45,"pin_x":398.0,"pin_y":172.0,"exit_vx":-1.11,"exit_vy":7.82},
    {"index":2,"time":0.88,"pin_x":386.0,"pin_y":332.0,"exit_vx":-0.95,"exit_vy":8.16},
    {"index":3,"time":1.05,"pin_x":388.0,"pin_y":371.0,"exit_vx":1.24,"exit_vy":7.90},
    {"index":4,"time":1.42,"pin_x":393.0,"pin_y":528.0,"exit_vx":-1.39,"exit_vy":8.68},
    {"index":5,"time":1.70,"pin_x":386.0,"pin_y":644.0,"exit_vx":-1.16,"exit_vy":8.95},
    {"index":6,"time":1.88,"pin_x":381.0,"pin_y":722.0,"exit_vx":-0.82,"exit_vy":5.00}
  ],
  "slot_hit": {
    "time": 2.50,
    "slot_center_x": 380.57,
    "slot_center_y": 812.70
  },
  "effects": {
    "particles_seed": 93514321,
    "coins_seed": 54123980
  }
}

