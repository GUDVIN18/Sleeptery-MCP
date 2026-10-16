import time


def current_time(func):
    async def wrapper(*args, **kwargs):
        a = time.time()
        result = await func(*args, **kwargs)
        b = time.time()
        print(f"Execution time: {b - a} seconds")
        return result
    return wrapper
        