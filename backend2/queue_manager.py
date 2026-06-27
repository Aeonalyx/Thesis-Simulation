from queue import Queue
from typing import List
from backend2.models import DocumentRequest

class QueueManager:
    def __init__(self):
        self.queue = Queue()

    def push(self, request: DocumentRequest):
        self.queue.put(request)

    def push_bulk(self, requests: List[DocumentRequest]):
        for r in requests:
            self.queue.put(r)

    def pop_all(self) -> List[DocumentRequest]:
        items = []
        while not self.queue.empty():
            items.append(self.queue.get())
        return items

    def size(self) -> int:
        return self.queue.qsize()