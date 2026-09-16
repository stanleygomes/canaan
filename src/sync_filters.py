from .db import upsert_search_filters
from .search import load_config
from .logger import logger


def main() -> None:
    filters = load_config()
    upsert_search_filters(filters)
    logger.info("🧭 Filtros sincronizados no PostgreSQL: default")


if __name__ == "__main__":
    main()
