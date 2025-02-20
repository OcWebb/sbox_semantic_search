import requests
from tenacity import retry, stop_after_attempt, wait_exponential


class FacepunchService:
    base_url: str

    def __init__(self, base_url: str):
        self.base_url = base_url

    def fetch_recently_updated_packages(self, take: int, skip: int) -> list[dict]:
        return self._inner_fetch_package("sort:updated", take, skip)
    
    def fetch_recently_created_packages(self, take: int, skip: int) -> list[dict]:
        return self._inner_fetch_package("sort:newest", take, skip)

    def fetch_all_packages(self) -> list[dict]:
        packages = []
        try:
            skip = 0
            while True:
                current_packages = self._inner_fetch_package("", 500, skip)
                packages.extend(current_packages)
                
                if len(current_packages) < 500:
                    break

                skip += 500
            
            return packages
        except requests.exceptions.RequestException as e:
            print("Error fetching data from facepunch backend.\nError:", e)
            return []
    
    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=1, max=10))
    def _inner_fetch_package(self, query: str, take: int, skip: int) -> list[dict]:
        """ Fetch packages from facepunch backend. """
        if take > 500:
            raise ValueError("Take must be less than or equal to 500")
        
        query_params = {
            "skip": skip, 
            "take": take,
            "q": query
        }
        response = requests.get(f"{self.base_url}/sbox/package/find/1/", params=query_params)
        response.raise_for_status()
        json_data = response.json()

        return json_data['Packages']
        
    def fetch_all_packages_from_file(self, filename: str) -> list[dict]:
        try:
            with open(filename, 'r') as f:
                import json
                return json.load(f)
        except FileNotFoundError:
            return []
