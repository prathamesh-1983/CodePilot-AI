import os
from openai import OpenAI

def get_client() -> OpenAI:
    key = os.getenv("NEBIUS_API_KEY", "").strip()
    if not key or key == "replace_with_your_token_factory_key":
        raise RuntimeError("NEBIUS_API_KEY is missing. Add your Token Factory key to backend/.env.")
    return OpenAI(
        api_key=key,
        base_url=os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.us-central1.nebius.com/v1/")
    )

def get_model() -> str:
    return os.getenv("NEBIUS_MODEL", "nvidia/nemotron-3-super-120b-a12b")
