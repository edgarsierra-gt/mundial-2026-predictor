from src.ingest.normalize_teams import make_team_id, normalize_team


def test_mexico_aliases_resolve_to_mex():
    assert make_team_id("Mexico") == "MEX"
    assert make_team_id("Mexico", "MEX") == "MEX"


def test_netherlands_aliases_resolve_to_ned():
    assert make_team_id("Netherlands") == "NED"
    assert make_team_id("Paises Bajos") == "NED"
    assert make_team_id("NED") == "NED"


def test_ivory_coast_aliases_resolve_to_civ():
    assert make_team_id("Costa de Marfil") == "CIV"
    assert make_team_id("Ivory Coast") == "CIV"
    assert make_team_id("CIV") == "CIV"


def test_turkiye_aliases_resolve_to_tur():
    assert make_team_id("Turquia") == "TUR"
    assert make_team_id("Turkiye") == "TUR"
    assert make_team_id("TUR") == "TUR"


def test_normalize_team_returns_slug():
    team = normalize_team("Estados Unidos")
    assert team.team_id == "USA"
    assert team.slug == "estados-unidos"

