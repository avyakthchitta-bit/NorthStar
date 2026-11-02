
import json
from pathlib import Path


DEFAULT_METADATA = {
    "display_name": "",
    "project_type": "Other",
    "description": "",
    "color": "#66e3c4",
    "icon": "◇"
}


class ProjectMetadataManager:

    def __init__(self, file_path=None):

        self.file_path = (
            Path(file_path)
            if file_path
            else Path(__file__).with_name("project_metadata.json")
        )

        self.metadata = {}
        self.load()

    # --------------------------------------------------
    # PATH HANDLING
    # --------------------------------------------------

    def normalize_path(self, project_path):

        return str(Path(project_path).resolve()).casefold()

    # --------------------------------------------------
    # LOAD AND SAVE
    # --------------------------------------------------

    def load(self):

        if not self.file_path.exists():
            self.metadata = {}
            return

        try:
            data = json.loads(
                self.file_path.read_text(encoding="utf-8")
            )

            if not isinstance(data, dict):
                raise ValueError("Invalid metadata format")

            self.metadata = {
                path: values
                for path, values in data.items()
                if isinstance(path, str)
                and isinstance(values, dict)
            }

        except (OSError, json.JSONDecodeError, ValueError):

            # Keep an empty metadata collection if loading fails.
            self.metadata = {}

    def save(self):

        try:
            self.file_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            temporary_file = self.file_path.with_suffix(
                self.file_path.suffix + ".tmp"
            )

            temporary_file.write_text(
                json.dumps(self.metadata, indent=4),
                encoding="utf-8"
            )

            temporary_file.replace(self.file_path)

            return True

        except OSError:
            return False

    # --------------------------------------------------
    # DEFAULTS
    # --------------------------------------------------

    def create_default(self, project_path):

        path = Path(project_path)

        metadata = DEFAULT_METADATA.copy()
        metadata["display_name"] = path.name

        return metadata

    # --------------------------------------------------
    # GET METADATA
    # --------------------------------------------------

    def get(self, project_path):

        key = self.normalize_path(project_path)

        if key not in self.metadata:
            return self.create_default(project_path)

        result = self.create_default(project_path)
        result.update(self.metadata[key])

        return result

    # --------------------------------------------------
    # UPDATE METADATA
    # --------------------------------------------------

    def update(self, project_path, new_metadata):

        if not isinstance(new_metadata, dict):
            return False

        key = self.normalize_path(project_path)

        updated = self.get(project_path)

        for field in DEFAULT_METADATA:

            if field in new_metadata:
                updated[field] = new_metadata[field]

        # Ensure the display name is never empty.
        if not str(updated["display_name"]).strip():
            updated["display_name"] = Path(project_path).name

        self.metadata[key] = updated

        return self.save()

    # --------------------------------------------------
    # REMOVE METADATA
    # --------------------------------------------------

    def remove(self, project_path):

        key = self.normalize_path(project_path)

        if key in self.metadata:
            del self.metadata[key]
            return self.save()

        return True
