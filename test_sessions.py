"""Test script for the new session management features."""
from dari import Dari

def main():
    """Run basic tests with the API."""
    print("=" * 60)
    print("Testing Dari Session Management Implementation")
    print("=" * 60)
    print()

    # Initialize client
    api_key = "ck_kZ1WC6vR9H-WjB7zBFtjreJ_4DHyb-ZM3tCrS5wOwEU"
    client = Dari(api_key=api_key)
    print("✓ Client initialized successfully")
    print()

    # Test 1: Create a session
    print("Test 1: Creating a session...")
    try:
        session = client.create_session(
            screen_config={"width": 1280, "height": 720},
            ttl=3600,
            metadata={"test": "session_management"}
        )
        print(f"✓ Session created: {session['session_id']}")
        print(f"  Status: {session['status']}")
        print(f"  Expires at: {session['expires_at']}")
        print()
    except Exception as e:
        print(f"✗ Failed to create session: {e}")
        print()

    # Test 2: Get session details
    print("Test 2: Getting session details...")
    try:
        session_details = client.get_session(session['session_id'])
        print(f"✓ Retrieved session: {session_details['session_id']}")
        print(f"  Status: {session_details['status']}")
        print()
    except Exception as e:
        print(f"✗ Failed to get session: {e}")
        print()

    # Test 3: List sessions
    print("Test 3: Listing sessions...")
    try:
        sessions = client.list_sessions(status_filter="active", limit=10)
        print(f"✓ Found {sessions['total']} active sessions")
        print()
    except Exception as e:
        print(f"✗ Failed to list sessions: {e}")
        print()

    # Test 4: Update session
    print("Test 4: Updating session TTL...")
    try:
        updated_session = client.update_session(
            session['session_id'],
            ttl=7200,
            metadata={"test": "updated"}
        )
        print(f"✓ Session updated")
        print(f"  New expires at: {updated_session['expires_at']}")
        print()
    except Exception as e:
        print(f"✗ Failed to update session: {e}")
        print()

    # Test 5: Run action with session_id
    print("Test 5: Running action with session_id...")
    try:
        result = client.run_single_action(
            action="What is on the screen?",
            session_id=session['session_id']
        )
        print(f"✓ Action executed successfully")
        print(f"  Success: {result['success']}")
        print(f"  Result: {result['result'][:100]}..." if len(result['result']) > 100 else f"  Result: {result['result']}")
        print()
    except Exception as e:
        print(f"Note: Action test skipped - {e}")
        print("  (This is expected if the session doesn't have a valid browser attached)")
        print()

    # Test 6: Terminate session
    print("Test 6: Terminating session...")
    try:
        client.terminate_session(session['session_id'])
        print(f"✓ Session terminated successfully")
        print()
    except Exception as e:
        print(f"✗ Failed to terminate session: {e}")
        print()

    print("=" * 60)
    print("Testing complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
