import os
import django

# Configure Django FIRST
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# NOW import Django-dependent modules
from documents.services.ingestion.ingestion_pipeline import (
    DocumentIngestionPipeline
)


def main():
    try:
        obj = DocumentIngestionPipeline()

        result = obj.run("21193e30c73242b5b480d672897123a7")

        print("\n===== INGESTION RESULT =====\n")
        # print(result)

        print("\n===== RESULT TYPE =====\n")
        print(type(result))

    except Exception as e:
        print("\n===== ERROR =====\n")
        print(str(e))


if __name__ == "__main__":
    main()