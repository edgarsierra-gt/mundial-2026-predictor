from src.model.poisson import outcome_probabilities, score_matrix


def test_score_matrix_has_no_negative_probabilities():
    matrix = score_matrix(1.2, 1.0)
    assert (matrix["probability"] >= 0).all()


def test_score_matrix_sums_to_one():
    matrix = score_matrix(1.2, 1.0)
    assert abs(matrix["probability"].sum() - 1) < 1e-9


def test_stronger_lambda_generally_increases_win_probability():
    matrix = score_matrix(1.8, 0.8)
    probs = outcome_probabilities(matrix)
    assert probs["team_a_win"] > probs["team_b_win"]


def test_equal_lambdas_are_symmetric():
    matrix = score_matrix(1.2, 1.2)
    probs = outcome_probabilities(matrix)
    assert abs(probs["team_a_win"] - probs["team_b_win"]) < 1e-9

