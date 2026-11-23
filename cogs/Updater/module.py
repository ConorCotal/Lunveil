import asyncio
import os
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands


GITHUB_REPOSITORY = "https://github.com/ConorCotal/Lunveil.git"
GITHUB_BRANCH = "main"
MAX_BACKUPS = 10
BACKUP_FILES = (
    Path(".env"),
    Path("config/config.yml"),
    Path("cogs/KP/database.json"),
    Path("cogs/NewTickets/database.json"),
    Path("cogs/PlayerList/player_list.txt"),
)


class UpdateError(Exception):
    pass


@dataclass(frozen=True)
class UpdateResult:
    backup_name: str
    commit: str
    updated: bool
    requirements_changed: bool


def _find_git_executable() -> str:
    executable = shutil.which("git")
    if executable:
        return executable

    if os.name == "nt":
        program_files = (
            os.environ.get("ProgramFiles"),
            os.environ.get("ProgramFiles(x86)"),
        )
        for directory in program_files:
            if not directory:
                continue
            for relative_path in (
                Path("Git/cmd/git.exe"),
                Path("Git/bin/git.exe"),
            ):
                candidate = Path(directory) / relative_path
                if candidate.is_file():
                    return str(candidate)

    raise UpdateError("Nie znaleziono Git. Zainstaluj Git i dodaj go do PATH.")


def _run_git(git: str, repository: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(
            [git, *arguments],
            cwd=repository,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise UpdateError("Polecenie Git przekroczyło limit czasu.") from error
    except OSError as error:
        raise UpdateError(f"Nie można uruchomić Git: {error}") from error

    if result.returncode:
        details = (result.stderr or result.stdout).strip()
        if not details:
            details = "Git zakończył polecenie błędem."
        raise UpdateError(details[-1200:])

    return result.stdout.strip()


def _prune_backups(backup_directory: Path) -> None:
    backups = sorted(
        backup_directory.glob("bot-backup-*.zip"),
        key=lambda backup: backup.name,
        reverse=True,
    )
    for old_backup in backups[MAX_BACKUPS:]:
        try:
            old_backup.unlink()
        except OSError as error:
            raise UpdateError(
                f"Nie udało się usunąć starej kopii {old_backup.name}: {error}"
            ) from error


def _create_backup(repository: Path) -> Path:
    backup_directory = repository / "backups"
    try:
        backup_directory.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise UpdateError(f"Nie można utworzyć folderu kopii zapasowych: {error}") from error

    files_to_backup = [
        (repository / relative_path, relative_path)
        for relative_path in BACKUP_FILES
        if (repository / relative_path).is_file()
    ]
    if not files_to_backup:
        raise UpdateError("Nie znaleziono plików do utworzenia kopii zapasowej.")

    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S-%f")
    backup_path = backup_directory / f"bot-backup-{timestamp}.zip"
    temporary_path = backup_directory / f".{backup_path.name}.tmp"

    try:
        with zipfile.ZipFile(temporary_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
            for source, relative_path in files_to_backup:
                archive.write(source, arcname=relative_path.as_posix())
        temporary_path.replace(backup_path)
    except (OSError, zipfile.LargeZipFile) as error:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError as cleanup_error:
            raise UpdateError(
                f"Tworzenie kopii nie powiodło się ({error}); "
                f"nie udało się też usunąć pliku tymczasowego: {cleanup_error}"
            ) from cleanup_error
        raise UpdateError(f"Nie udało się utworzyć kopii zapasowej: {error}") from error

    _prune_backups(backup_directory)
    return backup_path


def _update_repository() -> UpdateResult:
    repository = Path(__file__).resolve().parents[2]
    git = _find_git_executable()
    backup = _create_backup(repository)

    try:
        branch = _run_git(git, repository, "branch", "--show-current")
        if branch != GITHUB_BRANCH:
            raise UpdateError(
                f"Updater działa tylko na gałęzi {GITHUB_BRANCH}; aktualna: {branch or 'detached HEAD'}."
            )

        current_commit = _run_git(git, repository, "rev-parse", "HEAD")
        _run_git(
            git,
            repository,
            "fetch",
            "--no-tags",
            "--quiet",
            GITHUB_REPOSITORY,
            GITHUB_BRANCH,
        )
        target_commit = _run_git(git, repository, "rev-parse", "FETCH_HEAD")
        if target_commit == current_commit:
            return UpdateResult(backup.name, current_commit, False, False)

        changed_files = _run_git(
            git,
            repository,
            "diff",
            "--name-only",
            f"{current_commit}..{target_commit}",
            "--",
            "requirements.txt",
        )
        _run_git(git, repository, "merge", "--ff-only", "--no-edit", "FETCH_HEAD")
    except UpdateError as error:
        raise UpdateError(
            f"Kopia utworzona: {backup.name}. Aktualizacja przerwana: {error}"
        ) from error

    return UpdateResult(
        backup_name=backup.name,
        commit=target_commit,
        updated=True,
        requirements_changed=bool(changed_files),
    )


class Updater(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._update_lock = asyncio.Lock()

    @app_commands.command(
        name="update-bot",
        description="Zrób kopię danych i pobierz aktualizację z GitHuba.",
    )
    async def update_bot(self, interaction: discord.Interaction) -> None:
        if not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message(
                "Tylko właściciel bota może go aktualizować.",
                ephemeral=True,
            )
            return

        if self._update_lock.locked():
            await interaction.response.send_message(
                "Aktualizacja już trwa.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        async with self._update_lock:
            try:
                result = await asyncio.to_thread(_update_repository)
            except UpdateError as error:
                await interaction.followup.send(f"❌ {error}", ephemeral=True)
                return

        if not result.updated:
            await interaction.followup.send(
                f"Bot jest aktualny. Kopia zapasowa: `{result.backup_name}`.",
                ephemeral=True,
            )
            return

        message = (
            f"✅ Pobrano aktualizację `{result.commit[:7]}`. "
            f"Kopia zapasowa: `{result.backup_name}`.\n"
            "Zatrzymaj bota w terminalu (`Ctrl+C`) i uruchom ponownie przyciskiem ▶ w VS Code."
        )
        if result.requirements_changed:
            message += (
                "\nZmieniono `requirements.txt`; przed restartem zainstaluj zależności: "
                r"`.\.venv\Scripts\python.exe -m pip install -r requirements.txt`."
            )

        await interaction.followup.send(message, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Updater(bot))
