# Local storage and database

## Data directory

StoryForge keeps runtime data outside the source repository. The data root is resolved in this order:

1. `STORYFORGE_HOME`, when set.
2. A configured `storage.data_dir` value passed as `configured_root`.
3. `$XDG_DATA_HOME/storyforge-ai`, when `XDG_DATA_HOME` is set.
4. `~/.local/share/storyforge-ai`.

The `STORYFORGE_HOME` environment override always takes precedence. Use `DataPaths.from_root()` to supply an explicit location. Call `DataPaths.ensure()` to create the root and its `projects`, `models`, `assets`, `cache`, `backups`, and `logs` directories. Path resolution itself does not create files.

The database is `storyforge.db` in the data root. Large model and media files remain ordinary files; SQLite stores structured metadata and managed paths in later milestones.

## SQLite foundation

The standard-library `sqlite3` module is used; no new runtime dependency is required. `Database.initialize()` creates the schema and applies versioned migrations. Connections enable foreign keys and a bounded busy timeout. Migrations are serialized under a write lock and applied transactionally. WAL is requested for file-backed storage, with SQLite's selected mode left in place if the filesystem does not support it.

Schema version 1 contains:
- `projects`: project identity, name, status and timestamps.
- `generation_jobs`: project-linked job type, status, JSON payload, error field and timestamps.
- `schema_migrations`: applied schema versions.

The API currently supports initialization, integrity checks, project creation/listing/lookup, and generation-job creation/lookup. It is a persistence foundation, not yet the complete production job scheduler. Job claiming, retries, checkpoints, event history, asset records, backups and restore are future scoped tasks.

## Example

```python
from storyforge.storage import DataPaths, Database

paths = DataPaths.from_environment().ensure()
database = Database(paths.database)
database.initialize()

project = database.create_project("My first story")
job = database.create_generation_job(
    project["id"], "story_outline", {"language": "en"}
)
print(project["id"], job["id"])
```

The module performs no network access and does not download models or media.
