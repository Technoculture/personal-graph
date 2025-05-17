from personal_graph.memory import MemoryManager


def main() -> None:
    with MemoryManager() as memory:
        memory.store_event("Alice started a new job at Google.", {"date": "2024-07-14"})
        memory.store_event("Bob moved to Paris.", {"date": "2024-07-12"})

        events = memory.recall("Who started a new job?", k=1)
        for event in events:
            print(event)


if __name__ == "__main__":
    main()
