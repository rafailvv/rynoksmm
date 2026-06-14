import asyncio

from openai import OpenAI

from Bot.config import config


client = OpenAI(
    api_key=config.openrouter.api_key,
    base_url="https://openrouter.ai/api/v1",
)


def make_embedding(text: str) -> list[float]:
    if not client:
        return []

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding


async def make_embedding_safe(text: str) -> list[float] | None:
    if not text:
        return None

    try:
        embedding = await asyncio.to_thread(make_embedding, text)
    except Exception:
        return None

    return embedding or None
