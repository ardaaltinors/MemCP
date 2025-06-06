#!/usr/bin/env python3
"""
Test script to verify no race conditions exist in user context handling.
This simulates concurrent requests with different users.
"""

import asyncio
import uuid
from typing import List
from src.core.context import set_current_user_id, get_current_user_id, user_context


async def simulate_user_operation(user_id: uuid.UUID, operation_id: int) -> dict:
    """Simulate a user operation that takes some time."""
    # Set user context (simulating middleware)
    set_current_user_id(user_id)
    
    # Simulate some async work
    await asyncio.sleep(0.1)
    
    # Get user context (simulating memory operations)
    retrieved_user_id = get_current_user_id()
    
    # More async work
    await asyncio.sleep(0.1)
    
    # Final check
    final_user_id = get_current_user_id()
    
    return {
        "operation_id": operation_id,
        "original_user_id": str(user_id),
        "retrieved_user_id": str(retrieved_user_id),
        "final_user_id": str(final_user_id),
        "consistent": str(user_id) == str(retrieved_user_id) == str(final_user_id)
    }


async def test_concurrent_users():
    """Test multiple concurrent users to check for race conditions."""
    print("Testing concurrent user context handling...")
    
    # Create multiple users
    users = [uuid.uuid4() for _ in range(10)]
    
    # Create concurrent tasks
    tasks = [
        simulate_user_operation(user_id, i) 
        for i, user_id in enumerate(users)
    ]
    
    # Run all tasks concurrently
    results = await asyncio.gather(*tasks)
    
    # Check results
    all_consistent = True
    for result in results:
        if not result["consistent"]:
            print(f"❌ RACE CONDITION DETECTED: {result}")
            all_consistent = False
        else:
            print(f"✅ Operation {result['operation_id']}: User {result['original_user_id'][:8]}... - Consistent")
    
    if all_consistent:
        print("\n🎉 NO RACE CONDITIONS DETECTED - All operations maintained correct user context!")
    else:
        print("\n💥 RACE CONDITIONS DETECTED - User context is being corrupted!")
    
    return all_consistent


async def test_context_manager():
    """Test the user_context context manager."""
    print("\nTesting user_context context manager...")
    
    user1 = uuid.uuid4()
    user2 = uuid.uuid4()
    
    # Set initial context
    set_current_user_id(user1)
    initial_user = get_current_user_id()
    
    # Use context manager to temporarily change user
    with user_context(user2):
        context_user = get_current_user_id()
        await asyncio.sleep(0.1)  # Simulate async work
        
    # Check that context was restored
    restored_user = get_current_user_id()
    
    print(f"Initial user: {initial_user}")
    print(f"Context user: {context_user}")  
    print(f"Restored user: {restored_user}")
    
    if initial_user == restored_user and context_user == user2:
        print("✅ Context manager works correctly")
        return True
    else:
        print("❌ Context manager failed")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("USER CONTEXT RACE CONDITION TESTS")
    print("=" * 60)
    
    # Test 1: Concurrent users
    test1_passed = await test_concurrent_users()
    
    # Test 2: Context manager
    test2_passed = await test_context_manager()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Concurrent users test: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"Context manager test: {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED - No race conditions detected!")
    else:
        print("\n💥 SOME TESTS FAILED - Race conditions may exist!")


if __name__ == "__main__":
    asyncio.run(main()) 