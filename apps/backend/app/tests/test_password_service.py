from services.password_service import hash_password, verify_password


def test_hash_password_returns_non_empty_hash() -> None:
    password_hash = hash_password("editor-password")

    assert isinstance(password_hash, str)
    assert password_hash != ""
    assert password_hash != "editor-password"


def test_verify_password_returns_true_for_matching_pair() -> None:
    password_hash = hash_password("editor-password")

    assert verify_password("editor-password", password_hash) is True


def test_verify_password_returns_false_for_wrong_password() -> None:
    password_hash = hash_password("editor-password")

    assert verify_password("wrong-password", password_hash) is False


def test_verify_password_returns_false_for_none_hash() -> None:
    assert verify_password("editor-password", None) is False
