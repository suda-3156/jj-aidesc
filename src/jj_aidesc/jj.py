import subprocess
from dataclasses import dataclass
from pathlib import Path

from jj_aidesc.error import JJError


@dataclass
class Commit:
    """Represents a jj commit."""

    change_id: str
    commit_id: str
    empty: bool
    files: list[str]


class JJClient:
    """Wrapper for jj commands."""

    def __init__(self, repo_path: Path | None = None):
        self.repo_path = repo_path or Path.cwd()

    def _run(self, *args: str) -> str:
        """Run a jj command and return stdout."""
        result = subprocess.run(
            ["jj", *args],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise JJError(f"jj command failed: {result.stderr.strip()}")
        return result.stdout

    def get_commits_without_description(
        self, revset: str = "mutable()"
    ) -> list[Commit]:
        """Get commits without description that have changes."""
        # Template: change_id<TAB>commit_id<TAB>empty_status<TAB>files
        template = (
            'change_id.short() ++ "\\t" ++ '
            'commit_id.short() ++ "\\t" ++ '
            'if(empty, "empty", "has_changes") ++ "\\t" ++ '
            'self.diff().files().map(|f| f.path()).join(",") ++ "\\n"'
        )

        output = self._run(
            "log",
            "--no-graph",
            "-T",
            template,
            "-r",
            f'({revset}) & description(exact:"") & ~empty()',
        )

        commits = []
        for line in output.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                change_id = parts[0]
                commit_id = parts[1]
                empty = parts[2] == "empty"
                files = parts[3].split(",") if len(parts) > 3 and parts[3] else []
                commits.append(
                    Commit(
                        change_id=change_id,
                        commit_id=commit_id,
                        empty=empty,
                        files=files,
                    )
                )

        return commits

    def get_diff(self, revision: str) -> str:
        """Get diff for a revision in git format."""
        return self._run("diff", "--git", "-r", revision)

    def get_diff_summary(self, revision: str) -> str:
        """Get diff summary for a revision."""
        return self._run("diff", "-r", revision, "--summary")

    def set_description(self, description: str, revision: str) -> None:
        """Set description for a revision."""
        self._run("describe", "-r", revision, "-m", description)

    def get_existing_descriptions(
        self, revset: str = "mutable()", limit: int = 10
    ) -> list[str]:
        """Get existing descriptions for style analysis."""
        template = 'description ++ "\\n---SEPARATOR---\\n"'
        output = self._run(
            "log",
            "--no-graph",
            "-T",
            template,
            "-r",
            f'({revset}) & ~description(exact:"")',
            "-n",
            str(limit),
        )

        descriptions = []
        for desc in output.split("---SEPARATOR---"):
            desc = desc.strip()
            if desc:
                descriptions.append(desc)

        return descriptions

    def check_jj_available(self) -> bool:
        """Check if jj is available."""
        try:
            subprocess.run(
                ["jj", "version"],
                capture_output=True,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def is_in_repo(self) -> bool:
        """Check if current directory is in a jj repository."""
        try:
            self._run("root")
            return True
        except JJError:
            return False
