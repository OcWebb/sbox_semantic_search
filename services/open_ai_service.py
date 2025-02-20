from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class OpenAiService:
    embedding_model: str
    _openai_client: OpenAI

    def __init__(self, api_key: str, embedding_model: str):
        self.embedding_model = embedding_model
        self._openai_client = OpenAI(api_key=api_key)

    def get_embedding(self, text: str) -> tuple[list[float], int]:
        """ Get embedding and tokens used for a text string. """
        embeddings, total_tokens = self.get_embeddings([text])

        return (embeddings[0], total_tokens)

    def get_embeddings(self, text: list[str]) -> tuple[list[list[float]], int]:
        """ Get embeddings and tokens used for a list of text strings. """
        if len(text) > 2048:
            embeddings = []
            total_tokens = 0
            for i in range(0, len(text), 2048):
                current_embeddings, current_total_tokens = self._get_embeddings_with_retry(text[i:i+2048])
                embeddings.extend(current_embeddings)
                total_tokens += current_total_tokens
                
            return (embeddings, total_tokens)
        else:
            return self._get_embeddings_with_retry(text)
        
    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=1, max=10))
    def _get_embeddings_with_retry(self, texts: list[str]) -> tuple[list[list[float]], int]:
        """ Get embeddings with exponential retry. """
        if len(texts) > 2048:
            raise ValueError("Text length must be less than or equal to 2048")
        
        response = self._openai_client.embeddings.create(model=self.embedding_model, input=texts)
        total_tokens = response.usage.total_tokens
        embeddings = [data.embedding for data in response.data]

        return (embeddings, total_tokens)
    
    def token_cost(self, token_count: int) -> float:
        cost_per_million = {
            "text-embedding-3-small": 0.02,
            "text-embedding-3-large": 0.13
        }
        
        if self.embedding_model not in cost_per_million:
            raise ValueError(f"Model {self.embedding_model} not found in cost_per_million")

        return token_count * cost_per_million[self.embedding_model] / 1_000_000
