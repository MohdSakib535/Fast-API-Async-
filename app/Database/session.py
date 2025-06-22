from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
# from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

"""
echo=True
   It logs all the SQL statements generated and executed by SQLAlchemy to the console (stdout).

   ✅ Why use echo=True?
    Debugging: Helps you see the actual SQL queries being sent to the database.

    Performance tuning: Lets you inspect queries for performance bottlenecks.

    Development Insight: Understand how your ORM operations translate to SQL.
    """

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to False in production
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes

    )

# Async session maker
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


# Dependency for FastAPI

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

