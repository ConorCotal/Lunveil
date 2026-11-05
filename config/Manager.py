import yaml
from types import SimpleNamespace

class ConfigManager:
    def __init__(self, config_path: str = "config/config.yml"):
        with open(config_path, "r", encoding="utf-8") as file:
            raw_data = yaml.safe_load(file)
            
        # Zamieniamy słownik na obiekty z dostępem przez kropkę
        self._config = self._dict_to_namespace(raw_data)

    def _dict_to_namespace(self, data):
        """Rekurencyjnie zamienia dict na SimpleNamespace."""
        if isinstance(data, dict):
            # Mapujemy każdy klucz słownika na Namespace
            return SimpleNamespace(**{k: self._dict_to_namespace(v) for k, v in data.items()})
        elif isinstance(data, list):
            # Jeśli w configu jest lista (np. fields), przetwarzamy jej elementy
            return [self._dict_to_namespace(i) for i in data]
        else:
            return data

    def __getattr__(self, name):
        """Pozwala na bezpośredni dostęp np. config.KP"""
        return getattr(self._config, name)