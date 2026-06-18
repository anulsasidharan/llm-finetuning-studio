from core.security import hash_password, verify_password


def test_hash_password_differs_from_input() -> None:
    password = "correct-horse-battery-staple"
    hashed = hash_password(password)
    assert hashed != password


def test_verify_password_succeeds_for_correct_password() -> None:
    password = "correct-horse-battery-staple"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True


def test_verify_password_fails_for_wrong_password() -> None:
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("wrong-password", hashed) is False
