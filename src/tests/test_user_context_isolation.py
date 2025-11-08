"""
Test to verify user context isolation in MCP tools.
"""
import uuid
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastmcp import Context
from src.utils.mcp_context import get_user_id_from_context
from src.exceptions import AuthenticationError


def test_user_context_extraction():
    """Test that user_id is correctly extracted from context."""
    # Create mock context (not used by dependency but required by helper)
    ctx = Mock(spec=Context)

    # Create mock request with user
    mock_request = Mock()
    mock_user = Mock()
    mock_user.id = uuid.uuid4()
    mock_request.state.user = mock_user

    # Patch dependency to return our mock request
    with patch("src.utils.mcp_context.get_http_request", return_value=mock_request):
        # Extract user_id
        extracted_user_id = get_user_id_from_context(ctx)
    
    # Verify correct user_id was extracted
    assert extracted_user_id == mock_user.id
    print(f"✓ Successfully extracted user_id: {extracted_user_id}")


def test_no_context_raises_error():
    """Test that missing context raises appropriate error."""
    try:
        get_user_id_from_context(None)
        assert False, "Should have raised AuthenticationError"
    except AuthenticationError as e:
        assert "No context provided" in str(e)
        print("✓ Correctly raised error for missing context")


def test_no_request_raises_error():
    """Test that missing request raises appropriate error."""
    # Create mock context without request
    ctx = Mock(spec=Context)

    with patch("src.utils.mcp_context.get_http_request", return_value=None):
        try:
            get_user_id_from_context(ctx)
            assert False, "Should have raised AuthenticationError"
        except AuthenticationError as e:
            assert "No HTTP request found" in str(e)
            print("✓ Correctly raised error for missing request")


def test_no_user_raises_error():
    """Test that missing user raises appropriate error."""
    # Create mock context and request without user
    ctx = Mock(spec=Context)
    mock_request = Mock()
    mock_request.state = Mock(spec=[])  # No user attribute

    with patch("src.utils.mcp_context.get_http_request", return_value=mock_request):
        try:
            get_user_id_from_context(ctx)
            assert False, "Should have raised AuthenticationError"
        except AuthenticationError as e:
            assert "No authenticated user found" in str(e)
            print("✓ Correctly raised error for missing user")


async def test_concurrent_user_isolation():
    """Test that concurrent requests maintain user isolation."""
    
    async def simulate_request(user_id: uuid.UUID) -> uuid.UUID:
        """Simulate a request with a specific user_id."""
        # Create mock context for this request
        ctx = Mock(spec=Context)
        mock_request = Mock()
        mock_user = Mock()
        mock_user.id = user_id
        mock_request.state.user = mock_user

        # Small delay to simulate processing
        await asyncio.sleep(0.01)

        # Extract and return the user_id with dependency patched per-call
        with patch("src.utils.mcp_context.get_http_request", return_value=mock_request):
            return get_user_id_from_context(ctx)
    
    # Create multiple user IDs
    user_ids = [uuid.uuid4() for _ in range(5)]
    
    # Run concurrent requests
    tasks = [simulate_request(uid) for uid in user_ids]
    results = await asyncio.gather(*tasks)
    
    # Verify each request got its own user_id
    for i, (expected, actual) in enumerate(zip(user_ids, results)):
        assert expected == actual, f"User {i} context leaked: expected {expected}, got {actual}"
    
    print(f"✓ Successfully isolated {len(user_ids)} concurrent user contexts")


if __name__ == "__main__":
    print("Testing user context isolation...")
    
    # Run sync tests
    test_user_context_extraction()
    test_no_context_raises_error()
    test_no_request_raises_error()
    test_no_user_raises_error()
    
    # Run async test
    asyncio.run(test_concurrent_user_isolation())
    
    print("\n✅ All user context isolation tests passed!")
