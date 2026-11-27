"""Team colours keyed by Jolpica constructor ref."""

FALLBACK_COLOR = "#E10600"

TEAM_COLORS: dict[str, str] = {
    "mclaren": "#FF8000",
    "red_bull": "#3671C6",
    "ferrari": "#E8002D",
    "mercedes": "#27F4D2",
    "aston_martin": "#229971",
    "alpine": "#0093CC",
    "williams": "#64C4FF",
    "rb": "#6692FF",
    "sauber": "#52E252",
    "haas": "#B6BABD",
    "audi": "#F50537",
    "cadillac": "#C8A45D",
}


def team_color(ref: str) -> str:
    return TEAM_COLORS.get(ref, FALLBACK_COLOR)
