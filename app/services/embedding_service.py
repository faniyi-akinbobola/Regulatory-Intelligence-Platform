from sentence_transformers import SentenceTransformer


class EmbeddingService:

    def __init__(self, model_name: str = "BAAI/bge-base-en-v1.5"):
        self._model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> list[float]:
        return self._model.encode(text, normalize_embeddings=True).tolist()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=False,
        ).tolist()
