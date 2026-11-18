def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_nickname(nickname: str) -> str:
    """Acepta `@nick` (forma de la URL) pero se almacena sin `@` y en minúsculas."""
    return nickname.strip().removeprefix("@").lower()
