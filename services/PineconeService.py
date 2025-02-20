from datetime import datetime
from pinecone import Pinecone
from tenacity import retry, stop_after_attempt, wait_exponential

from models import PineconeVector

class PineconeService:
    _pinecone: Pinecone

    def __init__(self, api_key: str, index_name: str):
        self._pinecone = Pinecone(api_key=api_key)
        self._index = self._pinecone.Index(index_name)

    def upsert_embeddings(self, data: list[PineconeVector]):
        """ Upsert embeddings to the Pinecone index. """
        for i in range(0, len(data), 100):
            self._index.upsert(vectors=[vector.to_dict() for vector in data[i:i+100]])


    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=1, max=10))
    def _search_pinecone_with_retry(self, 
                                   embedding: list[float], 
                                   take: int, 
                                   skip: int, 
                                   filter_dict: dict) -> list[PineconeVector]:
        """ Semantic Search the Pinecone index with retry. """
        topk = take + skip
        response = self._index.query(
            vector=embedding,
            top_k=topk,
            include_values=True,
            include_metadata=True,
            filter=filter_dict
        )
        
        return [PineconeVector(
            id=result["id"],
            values=result["values"],
            metadata=result["metadata"]
        ) for result in response["matches"][skip:take+skip]]


    def search_pinecone(self, 
                        embedding: list[float], 
                        take: int, 
                        skip: int, 
                        filter_dict: dict) -> list[PineconeVector]:
        """ Semantic Search the Pinecone index """
        try:
            return self._search_pinecone_with_retry(embedding, take, skip, filter_dict)
        except Exception as e:
            print("Error searching Pinecone index.\nError:", e)
            raise e
    
    def fetch_packages_created_after(self, take: int, date: int) -> list[PineconeVector]:
        """ Fetch packages from Pinecone index ordered by date updated. """
        # fetch all and sort in code
        vector = []
        for i in range(1536):
            vector.append(0.0)

        response = self._index.query(
            vector=vector,
            top_k=take,
            include_values=False,
            include_metadata=True,
            filter={"Created": {"$gte": date}},
        )

        matches = response["matches"]
        matches.sort(key=lambda x: x["metadata"]["Created"], reverse=True)

        return matches
    
    def fetch_packages_updated_after(self, take: int, date: int) -> list[PineconeVector]:
        """ Fetch packages from Pinecone index ordered by date updated. """
        vector = []
        for i in range(1536):
            vector.append(0.0)

        response = self._index.query(
            vector=vector,
            top_k=take,
            include_values=False,
            include_metadata=True,
            filter={"Updated": {"$gte": date}},
        )

        matches = response["matches"]
        matches.sort(key=lambda x: x["metadata"]["Updated"], reverse=True)

        return matches
    
    def fetch_recently_created_packages(self, take: int) -> list[PineconeVector]:
        # We need to ensure we get back less than we asked for otherwise we cant guarantee the order
        date = int(datetime.now().timestamp())
        offset = 3600 * 12
        fetch_amount = max(take*2, 20)
        packages = []
        iterations = 0
        while len(packages) <= take and iterations < 10:
            packages = self.fetch_packages_created_after(fetch_amount, date - offset*iterations)
            offset *= 2
            iterations += 1

        iterations_2 = 0
        while len(packages) == fetch_amount and iterations_2 < 10:
            fetch_amount *= 2
            iterations_2 += 1
            packages = self.fetch_packages_created_after(fetch_amount, date - offset*iterations)
        
        print(f"Found {len(packages)} packages while searching for {fetch_amount} packages")
        print(f"It took {iterations + iterations_2} iterations to find {take} packages")
        
        return packages[:take]
    
    def fetch_recently_updated_packages(self, take: int) -> list[PineconeVector]:
        # We need to ensure we get back less than we asked for otherwise we cant guarantee the order
        date = int(datetime.now().timestamp())
        offset = 3600 * 12
        fetch_amount = max(take*2, 20)
        packages = []
        iterations = 0
        while len(packages) <= take and iterations < 10:
            packages = self.fetch_packages_updated_after(fetch_amount, date - offset*iterations)
            offset *= 2
            iterations += 1

        iterations_2 = 0
        while len(packages) == fetch_amount and iterations_2 < 10:
            fetch_amount *= 2
            iterations_2 += 1
            packages = self.fetch_packages_updated_after(fetch_amount, date - offset*iterations)
        
        print(f"Found {len(packages)} packages while searching for {fetch_amount} packages")
        print(f"It took {iterations + iterations_2} iterations to find {take} packages")
        
        return packages[:take]
        

    
    def delete_index(self):
        """ Delete the Pinecone index """
        self._index.delete(delete_all=True)