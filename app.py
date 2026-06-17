from threading import Lock
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from textblob import TextBlob


class ItemBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: float = Field(gt=0)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: float | None = Field(default=None, gt=0)


class Item(ItemBase):
    id: int


class DeleteItemResponse(BaseModel):
    deleted: bool
    item: Item


class MessageResponse(BaseModel):
    message: str


class SentimentResponse(BaseModel):
    original_text: str
    polarity: float
    subjectivity: float


def dump_model(model: BaseModel, **kwargs: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(**kwargs)
    return model.dict(**kwargs)


def copy_item(item: Item, update: dict[str, Any]) -> Item:
    if hasattr(item, "model_copy"):
        return item.model_copy(update=update)
    return item.copy(update=update)


class ItemStore:
    def __init__(self) -> None:
        self._items: dict[int, Item] = {}
        self._next_item_id = 1
        self._lock = Lock()

    def create(self, item: ItemCreate) -> Item:
        with self._lock:
            item_id = self._next_item_id
            self._next_item_id += 1

            stored_item = Item(id=item_id, **dump_model(item))
            self._items[item_id] = stored_item
            return stored_item

    def list(self) -> list[Item]:
        with self._lock:
            return list(self._items.values())

    def get(self, item_id: int) -> Item | None:
        with self._lock:
            return self._items.get(item_id)

    def update(self, item_id: int, item: ItemUpdate) -> Item | None:
        with self._lock:
            stored_item = self._items.get(item_id)
            if stored_item is None:
                return None

            updated_item = copy_item(stored_item, dump_model(item, exclude_unset=True))
            self._items[item_id] = updated_item
            return updated_item

    def delete(self, item_id: int) -> Item | None:
        with self._lock:
            return self._items.pop(item_id, None)


def get_or_404(item: Item | None) -> Item:
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


def create_app() -> FastAPI:
    app = FastAPI(title="Performance Testing Demo API")
    store = ItemStore()

    @app.get("/", response_model=MessageResponse)
    def index() -> MessageResponse:
        return MessageResponse(message="Hello World")

    @app.get("/comment/{text}", response_model=SentimentResponse)
    def get_comment(text: str) -> SentimentResponse:
        blob = TextBlob(text)
        return SentimentResponse(
            original_text=text,
            polarity=blob.sentiment.polarity,
            subjectivity=blob.sentiment.subjectivity,
        )

    @app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED)
    def create_item(item: ItemCreate) -> Item:
        return store.create(item)

    @app.get("/items", response_model=list[Item])
    def list_items() -> list[Item]:
        return store.list()

    @app.get("/items/{item_id}", response_model=Item)
    def get_item(item_id: int) -> Item:
        return get_or_404(store.get(item_id))

    @app.put("/items/{item_id}", response_model=Item)
    def update_item(item_id: int, item: ItemUpdate) -> Item:
        return get_or_404(store.update(item_id, item))

    @app.delete("/items/{item_id}", response_model=DeleteItemResponse)
    def delete_item(item_id: int) -> DeleteItemResponse:
        return DeleteItemResponse(deleted=True, item=get_or_404(store.delete(item_id)))

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)