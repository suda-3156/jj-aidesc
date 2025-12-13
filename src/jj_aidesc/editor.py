import os
import subprocess
import tempfile
from pathlib import Path

from jj_aidesc.error import AbortError

DEFAULT_EDITOR = "vim"


class Editor:
    def __init__(self, editor_cmd: str | None = None):
        self.editor_cmd = editor_cmd or os.environ.get("EDITOR", DEFAULT_EDITOR)

    def edit(self, initial_message: str = "") -> str:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(initial_message)
            f.write("\n\njj: Edit the commit description above.")
            f.write("\njj: Lines starting with 'jj:' will be ignored.")
            f.write("\njj: Leave empty or type 'abort' to cancel.")
            temp_path = Path(f.name)

        try:
            subprocess.run([self.editor_cmd, str(temp_path)], check=True)

            edited_content = temp_path.read_text()
            edited_message = self._clean_message(edited_content)

            if self._is_aborted(edited_message):
                raise AbortError("User aborted editing")

            return edited_message

        except subprocess.CalledProcessError as e:
            raise AbortError(f"Editor failed: {e}") from e
        finally:
            temp_path.unlink(missing_ok=True)

    def _clean_message(self, content: str) -> str:
        lines = []
        for line in content.split("\n"):
            if not line.strip().startswith("jj:"):
                lines.append(line)
        return "\n".join(lines).strip()

    def _is_aborted(self, message: str) -> bool:
        abort_markers = ["abort", "a", "cancel", "exit", "e", "quit", "q"]
        cleaned = message.strip().lower()
        return not cleaned or cleaned in abort_markers
