import json
import os
from datetime import datetime

MEMORY_FILE = "memory.json"

class MemoryManager:
    def __init__(self, memory_file=MEMORY_FILE):
        self.memory_file = memory_file

    def read_memories(self):
        """Reads memories from the memory file."""
        if not os.path.exists(self.memory_file):
            return []
        with open(self.memory_file, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def write_memories(self, memories):
        """Writes memories to the memory file."""
        with open(self.memory_file, "w") as f:
            json.dump(memories, f, indent=4)

    def retrieve_all(self):
        """Retrieves all stored memories."""
        return self.read_memories()

    def store(self, content: str, tags: list[str] | None = None) -> str:
        """Stores a new memory entry."""
        memories = self.read_memories()
        new_memory = {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "tags": tags if tags is not None else []
        }
        memories.append(new_memory)
        self.write_memories(memories)
        return "Memory stored successfully."