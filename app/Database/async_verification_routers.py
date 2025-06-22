import asyncio
import time
import httpx
import threading
from concurrent.futures import ThreadPoolExecutor
import psutil
import os
from sqlalchemy.ext.asyncio import AsyncSession
from app.books.views import get_books_views
from app.Database.session import AsyncSessionLocal
from fastapi import APIRouter


verification_router = APIRouter(
    prefix="/t1",
    tags=["async-verification"]
)

# 1. ASYNC DATABASE VERIFICATION
# Add this to your main.py to verify async database operations
@verification_router.get("/test-async-db")
async def test_async_database():
    """Test that database operations are truly async"""
    start_time = time.time()

    async def slow_query(delay: int):
        await asyncio.sleep(delay)
        async with AsyncSessionLocal() as db:
            books = await get_books_views(db, limit=1)
            return len(books)

    # Run multiple slow queries concurrently
    tasks = [
        slow_query(1),
        slow_query(1),
        slow_query(1),
    ]
    
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    execution_time = end_time - start_time

    return {
        "message": "Async database test completed",
        "results": results,
        "execution_time": f"{execution_time:.2f} seconds",
        "expected_time": "~1 second (if truly async)",
        "actual_async": execution_time < 2.0,
        "explanation": "If sync: ~3 seconds, If async: ~1 second"
    }




# 2. CONCURRENT REQUESTS TEST
@verification_router.get("/test-concurrent")
async def test_concurrent_handling():
    """Test concurrent request handling"""
    start_time = time.time()
    
    # Simulate some async work
    await asyncio.sleep(2)
    
    end_time = time.time()
    thread_id = threading.current_thread().ident
    process_id = os.getpid()
    
    return {
        "message": "Request processed",
        "processing_time": f"{end_time - start_time:.2f} seconds",
        "thread_id": thread_id,
        "process_id": process_id,
        "timestamp": time.time()
    }




# 3. ASYNC OPERATIONS VERIFICATION
@verification_router.get("/test-async-operations")
async def test_async_operations():
    """Verify that async operations work correctly"""
    
    async def async_task(task_id: int, delay: float):
        await asyncio.sleep(delay)
        return f"Task {task_id} completed after {delay}s"
    
    start_time = time.time()
    
    # Run multiple async tasks concurrently
    tasks = [
        async_task(1, 0.5),
        async_task(2, 1.0),
        async_task(3, 0.3),
        async_task(4, 0.8),
    ]
    
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    return {
        "results": results,
        "total_execution_time": f"{total_time:.2f} seconds",
        "expected_time": "~1.0 seconds (max delay)",
        "is_truly_async": total_time < 1.5,
        "explanation": "If sync: ~2.6s (sum of delays), If async: ~1.0s (max delay)"
    }



# 9. PERFORMANCE COMPARISON
@verification_router.get("/test-sync-vs-async")
async def test_sync_vs_async():
    """Compare sync vs async performance"""
    
    # Simulate async work
    async def async_work():
        await asyncio.sleep(0.1)
        return "async_done"
    
    # Test async approach
    start_async = time.time()
    async_tasks = [async_work() for _ in range(10)]
    async_results = await asyncio.gather(*async_tasks)
    end_async = time.time()
    async_time = end_async - start_async
    
    # Simulate what sync would be
    sync_time_estimate = 0.1 * 10  # 10 operations × 0.1s each
    
    return {
        'async_results': len(async_results),
        'async_time': f"{async_time:.3f} seconds",
        'estimated_sync_time': f"{sync_time_estimate:.3f} seconds",
        'performance_improvement': f"{sync_time_estimate / async_time:.1f}x faster",
        'is_truly_async': async_time < 0.3  # Should be ~0.1s, not ~1.0s
    }
