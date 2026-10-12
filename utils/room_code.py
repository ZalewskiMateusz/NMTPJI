import socket

# Unikalna lista 256 ikonicznych pojęć MTG (0-255)
MTG_WORDS = [
    # Planeswalkerzy & Legendy (0-49)
    "LOTUS", "JACE", "CHANDRA", "LILIANA", "GARRUK", "BOLAS", "ATRAXA", "KARN",
    "URZA", "MISRHRA", "SERRA", "TEFERI", "KOZIELK", "ULAMOG", "EMRAKUL", "AJANI",
    "SORIN", "NISSA", "VRASKA", "HUATLI", "SAHEELI", "SAMUT", "TAMAYO", "KAYA",
    "FAYDEN", "NARSET", "ASHIOK", "ZAREK", "DOMRI", "TYVAR", "LUKKA", "KOTH",
    "VENSAR", "ELSPETH", "NAHIRI", "GIDEON", "JAYA", "BALLARD", "NEHEB", "THRAXIMUNDAR",
    "PROSHH", "MARCHESA", "MULDROTHA", "YAROK", "KORVOLD", "CHULANE", "GOLOS", "KENRITH",
    "SISAY", "AVACYN",

    # Sfery & Miejsca (50-99)
    "RAVNICA", "ZENDIKAR", "INISTRAD", "MIRRODIN", "ALARA", "TARKIR", "KALADESH", "AMONKHET",
    "DOMINARIA", "PHYREXIA", "IXALAN", "THEROS", "ELDRAINE", "IKORIA", "KALDHEIM", "STRIXHAVEN",
    "KAMIGAWA", "CAPENNA", "BLOMBURROW", "DUSKMOURN", "SHADOWMOOR", "LORWYN", "FLARE", "TOLARIA",
    "URZABORG", "SHIVAN", "LLANOWAR", "KROOSA", "CABAL", "ACADEMY", "SANCTUM", "PANTHEON",
    "NYX", "SKROUGE", "OTARA", "TOWERS", "CITADEL", "STRONGHOLD", "CATACOMBS", "STEPPES",
    "OUTPOST", "BARRACKS", "LABORATORY", "WORKSHOP", "COLOSSEUM", "ARENA", "NECROPOLIS", "SPIRE",
    "MAZE", "MEANDER",

    # Gildie, Kliny, Sfery Kolorów (100-129)
    "BOROS", "DIMIR", "GOLGARI", "GRUUL", "AZORIUS", "IZZET", "ORZHOV", "RAKDOS",
    "SELESNYA", "SIMIC", "BANT", "ESPER", "GRIXIS", "JUND", "NAYA", "ABZAN",
    "JESKAI", "MARDU", "SULTAI", "TEMUR", "WITHERBLOOM", "SILVERQUILL", "PRISMARI", "LOREHOLD",
    "QUANDRIX", "RIVETEERS", "CABARETTI", "BROKERS", "OBSCURA", "MAESTROS",

    # Ikoniczne Karty, Artefakty & Czary (130-189)
    "SOLRING", "MOX", "NEKUSAR", "CRYPT", "ANESTHESIA", "BRAINSTORM", "PONDER", "PREORDAIN",
    "PROBE", "TIMETWISTER", "RHYSTIC", "CYCLONIC", "RHINO", "TUTOR", "PROXIMITY", "SMOTHERING",
    "DOCKSIDE", "THIELE", "OLLAMPH", "BOWMASTERS", "ONE RING", "MONOTONE", "CRATERHOOF", "DOUBLING",
    "TEFERIPROT", "HEROIC", "CYBERDRIVE", "FELIDAR", "PANHARMONICON", "PARADOX", "STAFF", "SWIFTFOOT",
    "LIGHTNING", "POD", "PORTAL", "CRUCIBLE", "ORB", "MANTLE", "SKULLCLAMP", "GREAVES",
    "MONOLITH", "DYNAMO", "CANDELABRA", "VAULT", "MIRROR", "LENS", "PALANTIR", "TRIOME",
    "FETCH", "SHOCKLAND", "BOUNCE", "CANOPY", "SLOWLAND", "FASTLAND", "CHECKLAND", "PAINLAND",
    "SURVEY", "PENTAD", "SPHERE", "MATRIX",

    # Stwory & Typy MTG (190-229)
    "ELDRAZI", "SLIVER", "GOYF", "PHYREXIAN", "KITHKIN", "MERFOLK", "SLIVERKING", "ATRAXAL",
    "DRAGON", "ANGEL", "DEMON", "HYDRA", "PHOENIX", "BEAST", "ELEMENTAL", "DINOSAUR",
    "ARCHON", "PRAETOR", "KRAKEN", "LEVIATHAN", "GARGANTUA", "TREANT", "GHOUL", "SPECTER",
    "LICH", "VAMPIRE", "WURM", "DJINN", "EFREET", "HOMUNCULUS", "MYR", "CONSTRUCT",
    "THOPTER", "PEGASUS", "BASILISK", "GORGON", "SLITH", "SCAVENGER", "WALL", "SHAPESHIFTER",

    # Mechaniki & Słowa Kluczowe MTG (230-255)
    "SCRY", "SURVEIL", "PROLIFERATE", "STORM", "CASCADE", "DREDGE", "MADNESS", "NINJUTSU",
    "DELVE", "EVOKE", "MUTATE", "EXALTED", "EXTORT", "KICKER", "OVERLOAD", "MONSTROSITY",
    "ECHO", "SUSPEND", "TRANSMUTE", "CYPHER", "EXPLOIT", "AFFINITY", "CONSPIRE", "GRAFT",
    "PERSIST", "UNDYING"
]

# Weryfikacja unikalności na etapie ładowania modułu
assert len(MTG_WORDS) == 256, f"MTG_WORDS musi mieć dokładnie 256 elementów, ma {len(MTG_WORDS)}"
assert len(set(MTG_WORDS)) == 256, "MTG_WORDS zawiera duplikaty!"

WORD_TO_BYTE = {word: i for i, word in enumerate(MTG_WORDS)}


def get_local_ip() -> str:
    """Pobiera prawdziwy lokalny adres IP w sieci LAN."""
    try:
        # Tworzymy gniazdo UDP i łączymy się na zewnętrzny IP, żeby OS wykrył aktywną kartę sieciową
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("1.1.1.1", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def encode_ip_to_code(ip_str: str = None) -> str:
    """Przekształca IP (np. '192.168.1.15') w kod słowny MTG."""
    if ip_str is None:
        ip_str = get_local_ip()

    try:
        octets = [int(part) for part in ip_str.split(".")]
        if len(octets) != 4:
            return "LOTUS-JACE-ZENDIKAR-RAVNICA"

        words = [MTG_WORDS[octet % 256] for octet in octets]
        return "-".join(words)
    except Exception:
        return "LOTUS-JACE-ZENDIKAR-RAVNICA"


def decode_code_to_ip(code_str: str) -> str:
    """Przekształca kod słowny MTG (lub surowe IP) na adres IP."""
    code_str = code_str.strip()

    if "." in code_str:
        return code_str

    cleaned_code = code_str.replace(" ", "-").upper()
    parts = [p for p in cleaned_code.split("-") if p]

    if len(parts) != 4:
        return "127.0.0.1"

    try:
        octets = []
        for word in parts:
            if word in WORD_TO_BYTE:
                octets.append(str(WORD_TO_BYTE[word]))
            else:
                return "127.0.0.1"
        return ".".join(octets)
    except Exception:
        return "127.0.0.1"