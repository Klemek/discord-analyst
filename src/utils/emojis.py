import re
import json
import logging
from os import path

EXTRA_EMOJI = {
    "thumbup": "1f44d",
    "thumbdown": "1f44e",
    "timer": "23f2-fe0f",
    "cowboy": "1f920",
    "clown": "1f921",
    "newspaper2": "1f5de-fe0f",
    "french_bread": "1f956",
    "nerd": "1f913",
    "zipper_mouth": "1f910",
    "salad": "1f957",
    "rolling_eyes": "1f644",
    "basketball_player": "26f9-fe0f-200d-2642-fe0f",
    "thinking": "1f914",
    "e_mail": "2709-fe0f",
    "slight_frown": "1f641",
    "skull_crossbones": "2620-fe0f",
    "hand_splayed": "1f590-fe0f",
    "speaking_head": "1f5e3-fe0f",
    "cross": "271d-fe0f",
    "crayon": "1f58d-fe0f",
    "head_bandage": "1f915",
    "rofl": "1f923",
    "flag_white": "1f3f3-fe0f",
    "slight_smile": "1f642",
    "fork_knife_plate": "1f37d-fe0f",
    "robot": "1f916",
    "hugging": "1f917",
    "biohazard": "2623-fe0f",
    "notepad_spiral": "1f5d2-fe0f",
    "lifter": "1f3cb-fe0f-200d-2642-fe0f",
    "race_car": "1f3ce-fe0f",
    "left_facing_fist": "1f91b",
    "right_facing_fist": "1f91c",
    "tools": "1f6e0-fe0f",
    "umbrella2": "2602-fe0f",
    "upside_down": "2b07-fe0f",
    "first_place": "1f947",
    "dagger": "1f5e1-fe0f",
    "fox": "1f98a",
    "menorah": "1f54e",
    "desktop": "1f5a5-fe0f",
    "motorcycle": "1f3cd-fe0f",
    "levitate": "1f574-fe0f",
    "cheese": "1f9c0",
    "fingers_crossed": "1f91e",
    "frowning2": "1f626",
    "microphone2": "1f399-fe0f",
    "flag_black": "1f3f4",
    "chair": "1FA91",
    "champagne_glass": "1F942",
    "raised_hand": "270B",
    "knife": "1F52A",
    "postal_horn": "1F4EF",
    "punch": "1F44A",
}

global_list = {}
unicode_list = []
regex = re.compile("(<a?:[\\w\\-\\~]+:\\d+>|:[\\w\\-\\~]+:)")


def load_emojis():
    global global_list, unicode_list, regex
    emoji_list = []
    with open(path.join(path.dirname(__file__), "emoji.json"), mode="r") as f:
        emoji_list = json.loads(f.readline().strip())
    for emoji in EXTRA_EMOJI:
        emoji_list += [{"short_name": emoji, "unified": EXTRA_EMOJI[emoji]}]
    unicode_list_escaped = []
    for emoji in emoji_list:
        shortname = emoji["short_name"]
        unified = emoji["unified"]
        if unified is not None and shortname is not None:
            unicode_escaped = "".join([f"\\U{c:0>8}" for c in unified.split("-")])
            unicode = bytes(unicode_escaped, "ascii").decode("unicode-escape")
            shortcode = shortname.replace("-", "_")
            global_list[unicode] = f":{shortcode}:"
            unicode_list += [unicode]
            unicode_list_escaped += [unicode_escaped]
    regex = re.compile(f"(<a?:\\w+:\\d+>|:\\w+:|{'|'.join(unicode_list_escaped)})")
    logging.info(f"loaded {len(unicode_list)} emojis")
