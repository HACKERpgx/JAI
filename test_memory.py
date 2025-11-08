# test_memory.py
from memory import JAIMemory
try:
    memory = JAIMemory()
    memory.remember_long_term("name", "Abdul Rahman", importance=0.8)
    print("Stored: name = Abdul Rahman")
    value = memory.recall_long_term("name")
    print(f"Recalled: {value}")
    results = memory.search_memories("name")
    print(f"Search results: {results}")
except Exception as e:
    print(f"Memory error: {e}")