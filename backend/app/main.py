from fastapi import FastAPI
import uvicorn

from app.config import get_settings

app = FastAPI(title="KTZH Digital Twin API", version="0.1.0")

settings = get_settings()

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/env-configs")
def env_configs() -> dict[str, str]:
    return settings.model_dump()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)