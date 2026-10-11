import asyncio

from openai import OpenAI

from Bot.config import config


client = OpenAI(
    api_key=config.openrouter.api_key,
    base_url="https://openrouter.ai/api/v1",
    max_retries=10,
)


def make_embedding(text: str) -> list[float]:
    if not client:
        return []

    response = client.embeddings.create(
        model=config.openrouter.embedding_model,
        input=text,
    )
    return response.data[0].embedding


async def make_embedding_safe(text: str) -> list[float] | None:
    if not text:
        return None

    max_attempts = 10

    for attempt in range(max_attempts):
        try:
            embedding = await asyncio.to_thread(make_embedding, text)
            return embedding or None

        except Exception as e:
            wait_time = min(2 ** attempt, 30)

            print(f"Embedding error, attempt {attempt + 1}/{max_attempts}: {e}")
            print(f"Retrying in {wait_time} seconds...")

            await asyncio.sleep(wait_time)

    return None
