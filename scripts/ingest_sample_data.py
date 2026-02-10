from backend.app.services.ingestion import ingest_all


def main() -> None:
  """
  Convenience script to ingest the sample support data into Endee.

  Run after Endee is up and the backend dependencies are installed:
      uvicorn backend.app.main:app --reload
      python -m scripts.ingest_sample_data
  """

  ingest_all()


if __name__ == "__main__":
  main()

