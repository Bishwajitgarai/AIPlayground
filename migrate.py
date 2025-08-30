import subprocess
from pathlib import Path
from app.core.db import SQLALCHEMY_DATABASE_URL, Base

ALEMBIC_DIR = Path("alembic")
ALEMBIC_INI = Path("alembic.ini")


def init_alembic():
    if not ALEMBIC_DIR.exists() or not ALEMBIC_INI.exists():
        print("📦 Initializing Alembic...")
        subprocess.run(["alembic", "init", "alembic"], check=True)
        print("✅ Alembic initialized.")

        env_path = ALEMBIC_DIR / "env.py"
        with open(env_path, "r") as f:
            content = f.read()

        content = content.replace(
            "target_metadata = None",
            "from app.core.db import Base\n"
            "target_metadata = Base.metadata"
        )

        content = content.replace(
            "engine = engine_from_config(",
            f"from app.core.db import SQLALCHEMY_DATABASE_URL\n"
            f"from sqlalchemy import create_engine\n"
            f"engine = create_engine(SQLALCHEMY_DATABASE_URL)\n"
            f"# engine = engine_from_config("
        )

        with open(env_path, "w") as f:
            f.write(content)

        # Update alembic.ini
        with open("alembic.ini", "r") as f:
            lines = f.readlines()
        with open("alembic.ini", "w") as f:
            for line in lines:
                if line.startswith("sqlalchemy.url"):
                    f.write(f"sqlalchemy.url = {SQLALCHEMY_DATABASE_URL}\n")
                else:
                    f.write(line)


def make_migration():
    print("🛠  Autogenerating migration script...")
    subprocess.run(["alembic", "revision", "--autogenerate", "-m", "Auto migration"], check=True)


def apply_migration():
    print("⬆  Applying migration to DB...")
    subprocess.run(["alembic", "upgrade", "head"], check=True)


def main():
    init_alembic()
    make_migration()
    apply_migration()
    print("✅ Database is now up-to-date with models.")


if __name__ == "__main__":
    main()
