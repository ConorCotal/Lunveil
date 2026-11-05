import json
import os
import asyncio
import tempfile
from types import SimpleNamespace
from typing import Any, Dict, List

class JSONDataManager:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.lock = asyncio.Lock()
        self._raw_data: Dict[str, Any] = {}
        self.data: SimpleNamespace = SimpleNamespace()
        
        os.makedirs(os.path.dirname(self.file_path) or ".", exist_ok=True)
        self._ensure_file_exists()
        self.reload()

    def _ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)

    def reload(self):
        """
        Ładuje lub odświeża dane bezpośrednio z pliku na dysku do pamięci RAM.
        
        Przykład użycia:
        >>> db.reload()  # Przydatne, gdy ręcznie edytujesz plik JSON podczas działania bota
        """
        with open(self.file_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        if not isinstance(loaded_data, dict):
            raise ValueError(f"JSON data must be an object: {self.file_path}")
        self._raw_data = loaded_data
        self.data = self._dict_to_namespace(self._raw_data)

    def _dict_to_namespace(self, data: Any) -> Any:
        if isinstance(data, dict):
            return SimpleNamespace(**{k: self._dict_to_namespace(v) for k, v in data.items()})
        elif isinstance(data, list):
            return [self._dict_to_namespace(i) for i in data]
        else:
            return data

    def _namespace_to_dict(self, data: Any) -> Any:
        if isinstance(data, SimpleNamespace):
            return {k: self._namespace_to_dict(v) for k, v in vars(data).items()}
        elif isinstance(data, list):
            return [self._namespace_to_dict(i) for i in data]
        else:
            return data

    async def save(self) -> None:
        """
        Asynchronicznie zapisuje (zrzuca) aktualny stan z pamięci RAM do pliku JSON.
        Musisz wywołać tę funkcję po dokonaniu zmian (dodaniu, edycji lub usunięciu), 
        aby zapisać je trwale na dysku.
        
        Przykład użycia:
        >>> db[interaction.user.id] = 987654321
        >>> await db.save()
        """
        async with self.lock:
            self._raw_data = self._namespace_to_dict(self.data)
            data_snapshot = self._raw_data
            loop = asyncio.get_running_loop()

            def write():
                directory = os.path.dirname(os.path.abspath(self.file_path))
                file_descriptor, temporary_path = tempfile.mkstemp(
                    dir=directory,
                    prefix=f".{os.path.basename(self.file_path)}.",
                    suffix=".tmp",
                )
                try:
                    with os.fdopen(file_descriptor, "w", encoding="utf-8") as f:
                        json.dump(data_snapshot, f, indent=4, ensure_ascii=False)
                        f.flush()
                        os.fsync(f.fileno())
                    os.replace(temporary_path, self.file_path)
                finally:
                    if os.path.exists(temporary_path):
                        os.unlink(temporary_path)

            await loop.run_in_executor(None, write)

    # ==========================================================================
    # --- INTERFEJS SŁOWNIKOWY (Magic Methods) ---
    # ==========================================================================

    def __getitem__(self, key: Any) -> Any:
        """
        Pobiera zawartość pliku JSON za pomocą nawiasów kwadratowych. 
        Automatycznie konwertuje wewnętrzne struktury SimpleNamespace na czytelne słowniki/listy.
        Zwraca None, jeśli klucz nie istnieje.
        
        Przykłady użycia:
        >>> thread_id = db[interaction.user.id]
        >>> print(thread_id)  # Wynik: 125624738593
        
        >>> user_stats = db["123456789"]
        >>> print(user_stats)  # Wynik: {'level': 5, 'xp': 120}
        """
        val = getattr(self.data, str(key), None)
        if isinstance(val, (SimpleNamespace, list)):
            return self._namespace_to_dict(val)
        return val

    def __setitem__(self, key: Any, value: Any) -> None:
        """
        Zapisuje lub aktualizuje dane w pamięci RAM przy użyciu nawiasów kwadratowych.
        Akceptuje typy proste (int, str, bool), listy oraz zagnieżdżone słowniki.
        
        Przykłady użycia:
        >>> # Zapis prostej wartości:
        >>> db[interaction.user.id] = interaction.channel_id
        
        >>> # Zapis listy (np. system ostrzeżeń):
        >>> db["user_warns"] = ["Spam na czacie", "Obraza gracza"]
        
        >>> # Zapis rozbudowanego słownika:
        >>> db[interaction.user.id] = {"status": "in_progress", "step": 2, "items": ["miecz", "tarcza"]}
        """
        setattr(self.data, str(key), self._dict_to_namespace(value))

    def __delitem__(self, key: Any) -> None:
        """
        Usuwa wskazany klucz z pamięci RAM za pomocą słowa kluczowego 'del'.
        
        Przykład użycia:
        >>> if interaction.user.id in db:
        >>>     del db[interaction.user.id]
        >>>     await db.save()  # Trwałe zapisanie usunięcia
        """
        key_str = str(key)
        if hasattr(self.data, key_str):
            delattr(self.data, key_str)

    def __len__(self) -> int:
        """
        Zwraca łączną liczbę głównych kluczy (rekordów) znajdujących się w pliku JSON.
        
        Przykład użycia:
        >>> total_sessions = len(db)
        >>> print(f"Obecnie otwartych wątków KP: {total_sessions}")
        """
        return len(vars(self.data))

    def __contains__(self, key: Any) -> bool:
        """
        Sprawdza, czy dany klucz istnieje w pliku JSON za pomocą operatora 'in'.
        Zwraca True lub False.
        
        Przykład użycia:
        >>> if interaction.user.id in db:
        >>>     print("Ten użytkownik ma już aktywny proces rekrutacji!")
        >>> else:
        >>>     print("Użytkownik nie figuruje w bazie danych.")
        """
        return hasattr(self.data, str(key))

    # ==========================================================================
    # --- ITERACJA I PRZEGLĄDANIE (Dict Methods) ---
    # ==========================================================================

    def keys(self) -> List[str]:
        """
        Zwraca listę wszystkich głównych kluczy w pliku JSON jako stringi.
        
        Przykład użycia:
        >>> all_users_in_db = db.keys()
        >>> print(all_users_in_db)  # Wynik: ['12345678', '98765432']
        """
        return list(vars(self.data).keys())

    def values(self) -> List[Any]:
        """
        Zwraca listę wszystkich wartości (zawartości kluczy) w pliku JSON.
        
        Przykład użycia:
        >>> all_active_threads = db.values()
        >>> print(all_active_threads)  # Wynik: [987654321, 5544332211]
        """
        return [self._namespace_to_dict(v) for v in vars(self.data).values()]

    def items(self) -> List[tuple]:
        """
        Zwraca listę krotek (klucz, wartość). Idealne do przeglądania bazy pętlą for.
        
        Przykład użycia (np. czyszczenie nieaktywnych wątków przy starcie bota):
        >>> for user_id, thread_id in db.items():
        >>>     print(f"Użytkownik o ID {user_id} posiada wątek: {thread_id}")
        """
        return [(k, self._namespace_to_dict(v)) for k, v in vars(self.data).items()]

    def clear(self) -> None:
        """
        Całkowicie czyści zawartość menedżera w pamięci RAM.
        
        Przykład użycia:
        >>> db.clear()
        >>> await db.save()  # Plik na dysku staje się pustym słownikiem '{}'
        """
        self.data = SimpleNamespace()
