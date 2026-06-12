MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}

DEFAULT_SECTIONS = [
    "Editorial",
    "Highlights",
    "Fragments",
    "Photos",
    "Readings",
    "Videos",
    "Communities",
    "Commented links",
    "Agenda",
    "Footer",
]

SECTION_FRAGMENTS = "Fragments"


def edition_title(period: str) -> str:
    year, month = map(int, period.split("-"))
    return f"Fedizine — {MONTH_NAMES[month]} {year}"


def month_label(period: str) -> str:
    year, month = map(int, period.split("-"))
    return f"{MONTH_NAMES[month]} {year}"
