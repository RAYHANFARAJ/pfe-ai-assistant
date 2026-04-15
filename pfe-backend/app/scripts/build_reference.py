import json
import logging

from app.core.logging_config import setup_logging
from app.services.elasticsearch.xtra_reference_service import XtraReferenceService


def main() -> None:
    log_file = setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=== Début du script de construction du référentiel ===")

    service = XtraReferenceService()
    result = service.run()

    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))

    logger.info("=== Fin du script ===")
    logger.info("Log disponible ici : %s", log_file)


if __name__ == "__main__":
    main()
