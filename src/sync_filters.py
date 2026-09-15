from .db import upsert_search_filters
from .search import load_config


def main() -> None:
    filters = load_config()
    upsert_search_filters(filters)
    print("Filtros sincronizados no PostgreSQL: default")


if __name__ == "__main__":
    main()
