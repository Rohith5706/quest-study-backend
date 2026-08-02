RANKS = [
    (0, "Novice"),
    (500, "Apprentice"),
    (1500, "Adept"),
    (3500, "Expert"),
    (7000, "Elite"),
    (13000, "Master"),
    (22000, "Grandmaster"),
    (35000, "Legend"),
    (55000, "Mythic"),
]

LEARNER_CLASSES = [
    "Chronomancer", "Codeweaver", "Algorithmist", "Tactician", "Archivist",
    "Strategist", "Runewright", "Cipher", "Logic Knight", "Mindsmith",
]


def get_rank(total_xp: int) -> str:
    current_rank = RANKS[0][1]
    for threshold, name in RANKS:
        if total_xp >= threshold:
            current_rank = name
        else:
            break
    return current_rank


def get_next_rank_threshold(total_xp: int):
    for threshold, name in RANKS:
        if total_xp < threshold:
            return threshold, name
    return None, None  # already at max rank (Mythic)
