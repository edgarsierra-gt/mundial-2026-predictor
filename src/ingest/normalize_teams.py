from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

try:
    from slugify import slugify as _slugify
except ImportError:  # pragma: no cover - dependency fallback
    _slugify = None


ALIAS_TO_ID = {
    "argentina": "ARG",
    "australia": "AUS",
    "austria": "AUT",
    "belgica": "BEL",
    "belgium": "BEL",
    "brazil": "BRA",
    "brasil": "BRA",
    "canada": "CAN",
    "colombia": "COL",
    "croacia": "CRO",
    "croatia": "CRO",
    "ecuador": "ECU",
    "egipto": "EGY",
    "egypt": "EGY",
    "france": "FRA",
    "francia": "FRA",
    "ghana": "GHA",
    "irak": "IRQ",
    "iraq": "IRQ",
    "jordania": "JOR",
    "jordan": "JOR",
    "noruega": "NOR",
    "norway": "NOR",
    "panama": "PAN",
    "paraguay": "PAR",
    "portugal": "POR",
    "senegal": "SEN",
    "tunez": "TUN",
    "tunisia": "TUN",
    "uruguay": "URU",
    "uzbekistan": "UZB",
    "mexico": "MEX",
    "mex": "MEX",
    "germany": "GER",
    "alemania": "GER",
    "ger": "GER",
    "ale": "GER",
    "algeria": "DZA",
    "argelia": "DZA",
    "dza": "DZA",
    "alg": "DZA",
    "saudi arabia": "KSA",
    "arabia saudi": "KSA",
    "arabia saudita": "KSA",
    "ksa": "KSA",
    "sau": "KSA",
    "cape verde": "CPV",
    "cabo verde": "CPV",
    "cpv": "CPV",
    "cap": "CPV",
    "england": "ENG",
    "inglaterra": "ENG",
    "eng": "ENG",
    "ing": "ENG",
    "scotland": "SCO",
    "escocia": "SCO",
    "sco": "SCO",
    "esc": "SCO",
    "iran": "IRI",
    "iri": "IRI",
    "ira": "IRI",
    "japan": "JPN",
    "japon": "JPN",
    "jpn": "JPN",
    "jap": "JPN",
    "new zealand": "NZL",
    "nueva zelanda": "NZL",
    "nzl": "NZL",
    "new": "NZL",
    "nue": "NZL",
    "spain": "ESP",
    "espana": "ESP",
    "esp": "ESP",
    "spa": "ESP",
    "sweden": "SWE",
    "suecia": "SWE",
    "swe": "SWE",
    "sue": "SWE",
    "morocco": "MAR",
    "marruecos": "MAR",
    "mar": "MAR",
    "mor": "MAR",
    "haiti": "HTI",
    "hti": "HTI",
    "hai": "HTI",
    "south africa": "RSA",
    "sudafrica": "RSA",
    "rsa": "RSA",
    "south korea": "KOR",
    "corea del sur": "KOR",
    "kor": "KOR",
    "czechia": "CZE",
    "czech republic": "CZE",
    "republica checa": "CZE",
    "cze": "CZE",
    "qatar": "QAT",
    "catar": "QAT",
    "qat": "QAT",
    "switzerland": "SUI",
    "suiza": "SUI",
    "sui": "SUI",
    "bosnia and herzegovina": "BIH",
    "bosnia y herzegovina": "BIH",
    "bih": "BIH",
    "united states": "USA",
    "estados unidos": "USA",
    "eeuu": "USA",
    "ee uu": "USA",
    "usa": "USA",
    "netherlands": "NED",
    "paises bajos": "NED",
    "holanda": "NED",
    "ned": "NED",
    "ivory coast": "CIV",
    "cote divoire": "CIV",
    "costa de marfil": "CIV",
    "civ": "CIV",
    "curacao": "CUW",
    "curazao": "CUW",
    "cuw": "CUW",
    "turkiye": "TUR",
    "turkey": "TUR",
    "turquia": "TUR",
    "tur": "TUR",
    "dr congo": "COD",
    "rd congo": "COD",
    "congo dr": "COD",
    "congo rd": "COD",
    "democratic republic of congo": "COD",
    "republica democratica del congo": "COD",
    "cod": "COD",
}


@dataclass(frozen=True)
class TeamName:
    team_id: str
    name: str
    slug: str


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def normalize_key(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"", "nan", "none", "nd"}:
        return ""
    text = strip_accents(text).lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def make_slug(value: object) -> str:
    text = str(value).strip()
    if _slugify:
        return _slugify(text)
    text = normalize_key(text).replace(" ", "-")
    return text or "unknown"


def make_team_id(name: object, fifa_code: object | None = None) -> str:
    key = normalize_key(name)
    if key in ALIAS_TO_ID:
        return ALIAS_TO_ID[key]

    code = normalize_key(fifa_code).upper()
    if code:
        code_key = normalize_key(code)
        if code_key in ALIAS_TO_ID:
            return ALIAS_TO_ID[code_key]
        if 2 <= len(code) <= 4:
            return code

    compact = re.sub(r"[^A-Z0-9]", "", strip_accents(str(name)).upper())
    return (compact[:3] or "UNK").ljust(3, "X")


def normalize_team(name: object, fifa_code: object | None = None) -> TeamName:
    raw_name = "" if name is None else str(name).strip()
    team_id = make_team_id(raw_name, fifa_code)
    visible = raw_name if raw_name and raw_name.lower() != "nan" else team_id
    return TeamName(team_id=team_id, name=visible, slug=make_slug(visible))
