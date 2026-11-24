from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import MetaData
from sqlalchemy.pool import NullPool
import os
import sys
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, String, JSON, Boolean
from shared.programas_catalog import PROGRAMAS

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "siga_suiza_2026")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

metadata = MetaData()
Base = declarative_base(metadata=metadata)

class TimeStampedMixin:
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BaseModel(Base, TimeStampedMixin):
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True)

class OutboxEvent(BaseModel):
    __tablename__ = "outbox_events"
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    published = Column(Boolean, default=False, index=True)

_is_test = (os.getenv("DB_NAME") == "siga_test") or ("pytest" in sys.modules)

if _is_test:
    engine = create_async_engine(DATABASE_URL, echo=False, poolclass=NullPool)
else:
    engine = create_async_engine(
        DATABASE_URL, 
        echo=False, 
        pool_size=10, 
        max_overflow=20, 
        pool_pre_ping=True, 
        pool_recycle=300
    )
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db
        except BaseException:
            await db.rollback()
            raise
        finally:
            await db.close()

async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
            for programa in PROGRAMAS:
                await conn.execute(text("""
                    INSERT INTO programas_estudio (id, nombre, codigo, duracion_periodos, creditos_totales, modalidad, estado)
                    VALUES (:id, :nombre, :codigo, 6, 126, 'presencial', 'activo')
                    ON CONFLICT (id) DO NOTHING
                """), programa)
            await conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conname = 'programas_estudio_id_oficial_check'
                          AND conrelid = 'programas_estudio'::regclass
                    ) THEN
                        ALTER TABLE programas_estudio
                        ADD CONSTRAINT programas_estudio_id_oficial_check CHECK (id BETWEEN 1 AND 11);
                    END IF;
                END $$;
            """))
            await conn.execute(text("SELECT setval(pg_get_serial_sequence('programas_estudio', 'id'), 11, true)"))
        print("Tablas creadas/verificadas")
    except Exception as e:
        print(f"init_db: tablas ya existen o error menor: {e}")