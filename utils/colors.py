from enum import IntEnum

class Colors(IntEnum):
    DEFAULT = 0x5865F2
    GREEN = 0x57F287
    YELLOW = 0xFEE75C
    FUCHSIA = 0xEB459E
    RED = 0xED4245
    SUCCESS = 0x43B581
    WARNING = 0xFAA61A
    ERROR = 0xF04747
    INFO = 0x3498DB
    PURPLE = 0x9B59B6
    ORANGE = 0xFF6F00
    PINK = 0xFF69B4
    TEAL = 0x1ABC9C
    GOLD = 0xF1C40F
    DARK_BLUE = 0x2C3E50
    LIGHT_GRAY = 0x95A5A6
    DARK_GRAY = 0x607D8B

    @classmethod
    def get(cls, name: str):
        """Bezpiecznie pobiera kolor po nazwie. Jeśli nie istnieje, zwraca DEFAULT."""
        try:
            # Klucze w Enumach są wielkimi literami, więc na wszelki wypadek dajemy .upper()
            return cls[name.upper()].value
        except KeyError:
            print(f"[Warning] Kolor '{name}' nie istnieje w klasie Colors. Używam DEFAULT.")
            return cls.DEFAULT.value