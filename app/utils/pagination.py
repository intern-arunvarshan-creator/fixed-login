def total_pages(total_items: int, limit: int) -> int:
    return (total_items + limit - 1) // limit
