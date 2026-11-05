import logging
from pathlib import Path
from typing import List, Optional, Tuple

from utils.JSONDataManager import JSONDataManager


logger = logging.getLogger("bot.kp")


class KPRepository:
    def __init__(self, file_path: str):
        self.file_path = str(Path(file_path).resolve())
        self._store = JSONDataManager(self.file_path)

    def records(self) -> List[Tuple[int, int]]:
        records = []
        for thread_id, owner_id in self._store.items():
            try:
                if isinstance(owner_id, dict):
                    owner_id = owner_id.get("owner_id")
                records.append((int(thread_id), int(owner_id)))
            except (TypeError, ValueError):
                logger.warning(
                    "Invalid KP database record thread_id=%r owner_id=%r",
                    thread_id,
                    owner_id,
                )
        return records

    def records_for_owner(self, owner_id: int) -> List[Tuple[int, int]]:
        return [
            (thread_id, record_owner_id)
            for thread_id, record_owner_id in self.records()
            if record_owner_id == owner_id
        ]

    def owner_for_thread(self, thread_id: int) -> Optional[int]:
        for record_thread_id, owner_id in self.records():
            if record_thread_id == thread_id:
                return owner_id
        return None

    def thread_name_for(self, thread_id: int) -> Optional[str]:
        value = self._store[str(thread_id)]
        if isinstance(value, dict):
            name = value.get("thread_name")
            return name if isinstance(name, str) and name else None
        return None

    async def migrate_legacy_records(self) -> int:
        migrated = 0
        for thread_id, value in self._store.items():
            if isinstance(value, dict):
                continue
            try:
                owner_id = int(value)
            except (TypeError, ValueError):
                logger.warning(
                    "Skipping invalid legacy KP database record thread_id=%r owner_id=%r",
                    thread_id,
                    value,
                )
                continue

            self._store[thread_id] = {
                "owner_id": owner_id,
                "thread_name": None,
            }
            migrated += 1

        if migrated:
            await self._store.save()
            logger.info(
                "Migrated legacy KP database records count=%s path=%s",
                migrated,
                self.file_path,
            )
        return migrated

    async def set_thread_name(self, thread_id: int, thread_name: str) -> None:
        owner_id = self.owner_for_thread(thread_id)
        if owner_id is None:
            raise KeyError(f"KP thread is not registered: {thread_id}")
        await self.register(thread_id, owner_id, thread_name)

    async def register(self, thread_id: int, owner_id: int, thread_name: Optional[str] = None) -> None:
        key = str(thread_id)
        previous_owner_id = self._store[key]
        self._store[key] = {
            "owner_id": owner_id,
            "thread_name": thread_name,
        }
        try:
            await self._store.save()
        except Exception:
            if previous_owner_id is None:
                del self._store[key]
            else:
                self._store[key] = previous_owner_id
            raise

    async def remove(self, thread_id: int) -> bool:
        key = str(thread_id)
        if key not in self._store:
            return False
        owner_id = self._store[key]
        del self._store[key]
        try:
            await self._store.save()
        except Exception:
            self._store[key] = owner_id
            raise
        return True
