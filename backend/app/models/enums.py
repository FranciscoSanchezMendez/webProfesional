from enum import StrEnum


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class ProfileVisibility(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"


class Language(StrEnum):
    ES = "es"
    EN = "en"
