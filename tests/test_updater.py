import tempfile
import unittest
import zipfile
from pathlib import Path

from cogs.Updater.module import _create_backup


class CreateBackupTests(unittest.TestCase):
    def test_backup_contains_existing_data_and_keeps_only_ten_archives(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory)
            files = {
                Path(".env"): "TOKEN=test-token",
                Path("config/config.yml"): "setting: test",
                Path("cogs/KP/database.json"): "{}",
                Path("cogs/NewTickets/database.json"): "{}",
            }
            for relative_path, contents in files.items():
                file_path = repository / relative_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(contents, encoding="utf-8")

            backup_directory = repository / "backups"
            backup_directory.mkdir()
            old_backups = [
                backup_directory / f"bot-backup-20200101-000000-{index:06}.zip"
                for index in range(10)
            ]
            for old_backup in old_backups:
                old_backup.touch()

            backup = _create_backup(repository)

            with zipfile.ZipFile(backup) as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {path.as_posix() for path in files},
                )
                self.assertEqual(archive.read(".env"), b"TOKEN=test-token")

            remaining_backups = list(backup_directory.glob("bot-backup-*.zip"))
            self.assertEqual(len(remaining_backups), 10)
            self.assertNotIn(old_backups[0], remaining_backups)


if __name__ == "__main__":
    unittest.main()
