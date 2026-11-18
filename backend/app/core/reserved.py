"""Nicknames no disponibles: rutas globales, términos de sistema y suplantación evidente."""

RESERVED_NICKNAMES: frozenset[str] = frozenset(
    {
        # rutas globales de la aplicación (FUNCTIONAL_REQUIREMENTS §1, §9)
        "login", "logout", "register", "signup", "signin", "about", "contact", "faq",
        "admin", "api", "assets", "static", "public", "media", "uploads", "images",
        "settings", "account", "profile", "profiles", "dashboard", "posts", "post",
        "auth", "me", "user", "users", "help", "support", "search", "explore",
        "terms", "privacy", "cookies", "legal", "sitemap", "robots", "favicon",
        "new", "edit", "delete", "home", "index", "health", "status",
        # términos de sistema y suplantación
        "root", "system", "administrator", "moderator", "staff", "official",
        "personalprofile", "null", "undefined", "anonymous", "www", "mail", "email",
    }
)  # fmt: skip


def is_reserved(nickname: str) -> bool:
    return nickname in RESERVED_NICKNAMES
