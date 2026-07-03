import logging

import app.models  # noqa: F401
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger(__name__)


def init_db() -> None:
    configure_logging()
    logger.info("Creating database tables from SQLAlchemy metadata")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema is ready")


if __name__ == "__main__":
    init_db()
