import random
from urllib.parse import quote

from locust import HttpUser, between, task


class AppUser(HttpUser):
    wait_time = between(0.5, 2.5)
    sample_comments = (
        "I love this product!",
        "I hate this product!",
        "I'm not sure about this product.",
    )

    def on_start(self):
        self.item_ids = []
        self.create_item()

    def _item_payload(self, prefix="Product"):
        return {
            "name": f"{prefix} {random.randint(1, 10000)}",
            "description": "Performance test item",
            "price": round(random.uniform(10, 500), 2),
        }

    def _random_item_id(self):
        if not self.item_ids:
            return None
        return random.choice(self.item_ids)

    @task(1)
    def index_page(self):
        self.client.get("/", name="/")

    @task(1)
    def sentiment_page(self):
        sentence = random.choice(self.sample_comments)
        self.client.get(f"/comment/{quote(sentence)}", name="/comment/{text}")

    @task(1)
    def create_item(self):
        payload = self._item_payload()

        with self.client.post("/items", json=payload, catch_response=True) as response:
            if response.status_code != 201:
                response.failure(f"Expected 201, got {response.status_code}")
                return
            self.item_ids.append(response.json()["id"])

    @task(3)
    def list_items(self):
        self.client.get("/items", name="/items")
id = self._random_item_id()
        if item_id is None:
            r
    @task(4)
    def get_item(self):
        item_eturn

        self.client.get(f"/items/{item_id}", name="/items/{item_id}")

    @task(2)
    def update_item(self):
        item_id = self._random_item_id()
        if item_id is None:
            return

        payload = self._item_payload(prefix="Updated Product")

        self.client.put(f"/items/{item_id}", json=payload, name="/items/{item_id}")

    @task(1)
    def delete_item(self):
        if not self.item_ids:
            return

        item_id = self.item_ids.pop()
        with self.client.delete(
            f"/items/{item_id}",
            name="/items/{item_id}",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Expected 200, got {response.status_code}")