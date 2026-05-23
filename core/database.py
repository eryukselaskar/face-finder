import sqlite3
import pickle
from pathlib import Path

_DB = Path.home() / ".face_finder" / "index.db"


def _conn():
    _DB.parent.mkdir(exist_ok=True)
    return sqlite3.connect(str(_DB))


def init():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS faces (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            folder    TEXT NOT NULL,
            encoding  BLOB NOT NULL
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS ix_fp ON faces(file_path)")
        c.execute("""CREATE TABLE IF NOT EXISTS folders (
            folder     TEXT PRIMARY KEY,
            file_count INTEGER DEFAULT 0,
            face_count INTEGER DEFAULT 0,
            indexed_at TEXT DEFAULT (datetime('now','localtime'))
        )""")


def clear_folder(folder: str):
    with _conn() as c:
        c.execute("DELETE FROM faces WHERE folder=?", (folder,))
        c.execute("DELETE FROM folders WHERE folder=?", (folder,))


def clear_all():
    with _conn() as c:
        c.execute("DELETE FROM faces")
        c.execute("DELETE FROM folders")


def insert_faces(file_path: str, folder: str, encodings: list):
    with _conn() as c:
        c.executemany(
            "INSERT INTO faces(file_path,folder,encoding) VALUES(?,?,?)",
            [(file_path, folder, pickle.dumps(e)) for e in encodings],
        )


def save_folder_stats(folder: str, file_count: int, face_count: int):
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO folders(folder,file_count,face_count) VALUES(?,?,?)",
            (folder, file_count, face_count),
        )


def get_all_encodings():
    with _conn() as c:
        rows = c.execute("SELECT file_path, folder, encoding FROM faces").fetchall()
    return [(fp, fd, pickle.loads(enc)) for fp, fd, enc in rows]


def get_folders():
    with _conn() as c:
        return c.execute(
            "SELECT folder, file_count, face_count FROM folders ORDER BY indexed_at DESC"
        ).fetchall()


def get_stats():
    with _conn() as c:
        files = c.execute("SELECT COUNT(DISTINCT file_path) FROM faces").fetchone()[0]
        faces = c.execute("SELECT COUNT(*) FROM faces").fetchone()[0]
    return files, faces
