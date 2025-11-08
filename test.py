

import time

import random, math, json

import settings


dd3 = {
  'id': 6016823284148995274,
  'name': 'SnoopDogg-335446',
  'title': 'Snoop Dogg',
  'link': 'https://t.me/nft/SnoopDogg-335446',
  'owner': None,
  'caption': None,
  'attributes': [
    {
      'name': 'Funky Homie',
      'type': 'GiftAttributeType.MODEL',
      'rarity': 25,
      'main': 'https://s3.catiton.app/media/gifts/komarovskij91/6016823284148995274/attributes/Funky Homie/main/6016823284148995274_Funky_Homie.tgs',
      'thumb_0': 'https://s3.catiton.app/media/gifts/komarovskij91/6016823284148995274/attributes/Funky Homie/thumb/6016823284148995274_Funky_Homie_thumb0.webp'
    },
    {
      'name': 'Heater Shield',
      'type': 'GiftAttributeType.SYMBOL',
      'rarity': 5,
      'main': 'https://s3.catiton.app/media/gifts/komarovskij91/6016823284148995274/attributes/Heater Shield/main/6016823284148995274_Heater_Shield.tgs',
      'thumb_0': 'https://s3.catiton.app/media/gifts/komarovskij91/6016823284148995274/attributes/Heater Shield/thumb/6016823284148995274_Heater_Shield_thumb0.webp'
    },
    {
      'name': 'Khaki Green',
      'type': 'GiftAttributeType.BACKDROP',
      'rarity': 15
    }
  ],
  'link_img': '',
  'link_tgs': '',
  'cloudflare_urls': {
    'Funky Homie_main': 'https://s3.catiton.app/media/gifts/komarovskij91/6016823284148995274/attributes/Funky Homie/main/6016823284148995274_Funky_Homie.tgs',
    'Funky Homie_thumb': 'https://s3.catiton.app/media/gifts/komarovskij91/6016823284148995274/attributes/Funky Homie/thumb/6016823284148995274_Funky_Homie_thumb0.webp',
    'Heater Shield_main': 'https://s3.catiton.app/media/gifts/komarovskij91/6016823284148995274/attributes/Heater Shield/main/6016823284148995274_Heater_Shield.tgs',
    'Heater Shield_thumb': 'https://s3.catiton.app/media/gifts/komarovskij91/6016823284148995274/attributes/Heater Shield/thumb/6016823284148995274_Heater_Shield_thumb0.webp'
  },
  'new_style': 'style',

  "gift_beats": {
    "power": 0,
    "rar": ""
  },
    "price": 0

}

# рандомный айди
def idrr0():
    rr = "AEIOUYBCDFGHJKLMNPQRSTVWXZaeiouybcdfghjklmnpqrstvwxz"
    return f"{int(time.time())}{random.choice(rr)}{random.choice(rr)}{random.choice(rr)}{random.choice(rr)}{random.choice(rr)}"




def gen_item(type_rar):

    id_n = idrr0()

    new_gift = dd3.copy()

    new_gift["id"] = f"{id_n}"
    new_gift["name"] = f"Gift Beats {type_rar}"
    new_gift["title"] = f"Gift {type_rar}"



    new_gift["new_style"] = random.choice(settings.user_style)


    if type_rar == "Common":

        new_gift["price"] = round(0.8 + (random.randint(1, 4) / 10), 1)
        new_gift["gift_beats"]["power"] = 5
        new_gift["gift_beats"]["rar"] = "Common"
        new_gift["attributes"] = [
        {
          'name': 'Gift Beats Common',
          'type': 'GiftAttributeType.MODEL',
          'rarity': 25,

          # TGS
          'main': "https://s3.catiton.app/SFERA_1.json",

          # картинка
          'thumb_0': 'https://s3.catiton.app/sf1.webp'
        },
        {
          'name': 'Gift Beats',
          'type': 'GiftAttributeType.SYMBOL',
          'rarity': 5,
          'main': 'https://s3.catiton.app/media/gifts/komarovskij91/6016823284148995274/attributes/Heater Shield/main/6016823284148995274_Heater_Shield.tgs',
          'thumb_0': 'https://s3.catiton.app/media/gifts/komarovskij91/6016823284148995274/attributes/Heater Shield/thumb/6016823284148995274_Heater_Shield_thumb0.webp'
        },
        {
          'name': 'Gift Beats',
          'type': 'GiftAttributeType.BACKDROP',
          'rarity': 15
        }
      ]

    if type_rar == "Uncommon":
        new_gift["price"] = random.randint(10, 25)
        new_gift["gift_beats"]["power"] = 20
        new_gift["gift_beats"]["rar"] = "Uncommon"
        new_gift["attributes"] = [
        {
          'name': 'Gift Beats Uncommon',
          'type': 'GiftAttributeType.MODEL',
          'rarity': 25,

          # TGS
          'main': "https://s3.catiton.app/SFERA_2.json",
          # картинка
          'thumb_0': 'https://s3.catiton.app/sf2.webp'
        },
        {
          'name': 'Gift Beats',
          'type': 'GiftAttributeType.SYMBOL',
          'rarity': 5,
          'main': 'https://s3.catiton.app/media/gifts/komarovskij91/6016823284148995274/attributes/Heater Shield/main/6016823284148995274_Heater_Shield.tgs',
          'thumb_0': 'https://s3.catiton.app/media/gifts/komarovskij91/6016823284148995274/attributes/Heater Shield/thumb/6016823284148995274_Heater_Shield_thumb0.webp'
        },
        {
          'name': 'Gift Beats',
          'type': 'GiftAttributeType.BACKDROP',
          'rarity': 15
        }
      ]

    if type_rar == "Rare":
        new_gift["price"] = random.randint(10, 25)
        new_gift["gift_beats"]["power"] = 23
        new_gift["gift_beats"]["rar"] = "Rare"
        new_gift["attributes"] = [
        {
          'name': 'Gift Beats Rare',
          'type': 'GiftAttributeType.MODEL',
          'rarity': 25,

          # TGS
          'main': "https://s3.catiton.app/SFERA_3.json",

          # картинка
          'thumb_0': 'https://s3.catiton.app/sf3.webp'
        },
        {
          'name': 'Gift Beats',
          'type': 'GiftAttributeType.SYMBOL',
          'rarity': 5,
          'main': 'https://s3.catiton.app/media/gifts/komarovskij91/6016823284148995274/attributes/Heater Shield/main/6016823284148995274_Heater_Shield.tgs',
          'thumb_0': 'https://s3.catiton.app/media/gifts/komarovskij91/6016823284148995274/attributes/Heater Shield/thumb/6016823284148995274_Heater_Shield_thumb0.webp'
        },
        {
          'name': 'Gift Beats',
          'type': 'GiftAttributeType.BACKDROP',
          'rarity': 15
        }
      ]

    if type_rar == "Epic":
        new_gift["price"] = random.randint(40, 50)
        new_gift["gift_beats"]["power"] = 28
        new_gift["gift_beats"]["rar"] = "Epic"
        new_gift["attributes"] = [
        {
          'name': 'Gift Beats Epic',
          'type': 'GiftAttributeType.MODEL',
          'rarity': 25,

          # TGS
          'main': "https://s3.catiton.app/SFERA_4.json",

          # картинка
          'thumb_0': 'https://s3.catiton.app/sf4.webp'
        },
        {
          'name': 'Gift Beats',
          'type': 'GiftAttributeType.SYMBOL',
          'rarity': 5,
          'main': 'https://s3.catiton.app/media/gifts/komarovskij91/6016823284148995274/attributes/Heater Shield/main/6016823284148995274_Heater_Shield.tgs',
          'thumb_0': 'https://s3.catiton.app/media/gifts/komarovskij91/6016823284148995274/attributes/Heater Shield/thumb/6016823284148995274_Heater_Shield_thumb0.webp'
        },
        {
          'name': 'Gift Beats',
          'type': 'GiftAttributeType.BACKDROP',
          'rarity': 15
        }
      ]

    if type_rar == "Mythic":
        new_gift["price"] = random.randint(400, 500)
        new_gift["gift_beats"]["power"] = 39
        new_gift["gift_beats"]["rar"] = "Mythic"
        new_gift["attributes"] = [
        {
          'name': 'Gift Beats Mythic',
          'type': 'GiftAttributeType.MODEL',
          'rarity': 25,

          # TGS
          'main': "https://s3.catiton.app/SFERA_5.json",

          # картинка
          'thumb_0': 'https://s3.catiton.app/sf5.webp'
        },
        {
          'name': 'Gift Beats',
          'type': 'GiftAttributeType.SYMBOL',
          'rarity': 5,
          'main': 'https://s3.catiton.app/media/gifts/komarovskij91/6016823284148995274/attributes/Heater Shield/main/6016823284148995274_Heater_Shield.tgs',
          'thumb_0': 'https://s3.catiton.app/media/gifts/komarovskij91/6016823284148995274/attributes/Heater Shield/thumb/6016823284148995274_Heater_Shield_thumb0.webp'
        },
        {
          'name': 'Gift Beats',
          'type': 'GiftAttributeType.BACKDROP',
          'rarity': 15
        }
      ]

    if type_rar == "Legendary":
        new_gift["price"] = random.randint(800, 902)
        new_gift["gift_beats"]["power"] = 44
        new_gift["gift_beats"]["rar"] = "Legendary"
        new_gift["attributes"] = [
        {
          'name': 'Gift Beats Legendary',
          'type': 'GiftAttributeType.MODEL',
          'rarity': 25,

          # TGS
          'main': "https://s3.catiton.app/SFERA_6.json",

          # картинка
          'thumb_0': 'https://s3.catiton.app/sf6.webp'
        },
        {
          'name': 'Gift Beats',
          'type': 'GiftAttributeType.SYMBOL',
          'rarity': 5,
          'main': 'https://s3.catiton.app/media/gifts/komarovskij91/6016823284148995274/attributes/Heater Shield/main/6016823284148995274_Heater_Shield.tgs',
          'thumb_0': 'https://s3.catiton.app/media/gifts/komarovskij91/6016823284148995274/attributes/Heater Shield/thumb/6016823284148995274_Heater_Shield_thumb0.webp'
        },
        {
          'name': 'Gift Beats',
          'type': 'GiftAttributeType.BACKDROP',
          'rarity': 15
        }
      ]


    data = {
        "id": f"gift:{id_n}",
        "gift": new_gift
    }


    return data


ff = ["1", "2", "3"]

fff = []