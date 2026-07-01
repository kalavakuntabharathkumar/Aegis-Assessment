import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "interview.db")


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                candidate_name TEXT NOT NULL,
                role TEXT NOT NULL,
                extracted_skills TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'in_progress',
                experience_level TEXT NOT NULL DEFAULT 'intermediate',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                question_index INTEGER NOT NULL,
                question TEXT NOT NULL,
                topic TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                question_id INTEGER NOT NULL,
                answer TEXT NOT NULL,
                score INTEGER,
                feedback TEXT,
                strength TEXT,
                improvement TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id),
                FOREIGN KEY (question_id) REFERENCES questions(id)
            )
        """)
        await db.commit()

        # Safely add new columns to existing databases
        for col, typedef in [
            ("score", "INTEGER"),
            ("feedback", "TEXT"),
            ("strength", "TEXT"),
            ("improvement", "TEXT"),
        ]:
            try:
                await db.execute(f"ALTER TABLE answers ADD COLUMN {col} {typedef}")
                await db.commit()
            except Exception:
                pass

        try:
            await db.execute("ALTER TABLE sessions ADD COLUMN experience_level TEXT DEFAULT 'intermediate'")
            await db.commit()
        except Exception:
            pass

        # Users table for JWT auth (role-based access control ready)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                full_name TEXT DEFAULT '',
                role TEXT NOT NULL DEFAULT 'candidate',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

        # Link sessions to users (optional — existing sessions keep user_id NULL)
        try:
            await db.execute("ALTER TABLE sessions ADD COLUMN user_id INTEGER REFERENCES users(id)")
            await db.commit()
        except Exception:
            pass

        # Traceability: store the RAG chunks used to generate each question
        try:
            await db.execute("ALTER TABLE questions ADD COLUMN source_chunks TEXT")
            await db.commit()
        except Exception:
            pass
