from app import create_app
from app.services.connection_service import send_request, accept_request, search_users, get_connection_status
from app.services.auth_service import create_user
from app.database.connection import get_db_connection

app = create_app()

with app.app_context():
    conn = get_db_connection()
    user_a_id = None
    user_b_id = None
    
    try:
        with conn.cursor() as cur:
            # Cleanup
            cur.execute("DELETE FROM connections WHERE user_id_1 IN (9999, 9998) OR user_id_2 IN (9999, 9998)")
            cur.execute("DELETE FROM users WHERE email IN ('test_a@example.com', 'test_b@example.com')")
            # Remove profiles too if needed but let's just ignore old ones
            cur.execute("DELETE FROM profiles WHERE user_id IN (SELECT user_id FROM users WHERE email IN ('test_a@example.com', 'test_b@example.com'))")
            conn.commit()

            # Create dummy users manually to get IDs
            user_a_id = create_user('Test A', 'test_a@example.com', 'Password123')
            user_b_id = create_user('Test B', 'test_b@example.com', 'Password123')
            
            # Insert Profiles (required for search_users JOIN)
            cur.execute("INSERT INTO profiles (user_id, headline) VALUES (%s, %s)", (user_a_id, 'Tester A'))
            cur.execute("INSERT INTO profiles (user_id, headline) VALUES (%s, %s)", (user_b_id, 'Tester B'))
            conn.commit()
            
            print(f"Created User A: {user_a_id}, User B: {user_b_id}")

        # 1. Verify initial status
        res = search_users('Test B', user_a_id)
        if not res:
            print("Search failed: User B not found")
            exit(1)
            
        status_a = res[0]['connection_status']
        print(f"Initial Status (A->B): {status_a}")
        assert status_a == 'none'

        # 2. Send Request A -> B
        success, msg = send_request(user_a_id, user_b_id)
        print(f"Send Request (A->B): success={success}, msg={msg}")
        assert success

        # 3. Verify status after request
        res = search_users('Test B', user_a_id)
        status_a = res[0]['connection_status']
        print(f"Status after request (A->B): {status_a}")
        assert status_a == 'pending_sent'

        res = search_users('Test A', user_b_id)
        status_b = res[0]['connection_status']
        print(f"Status for recipient (B->A): {status_b}")
        assert status_b == 'pending_received'

        # Get connection ID
        with conn.cursor() as cur:
            cur.execute("SELECT connection_id FROM connections WHERE (user_id_1=%s AND user_id_2=%s) OR (user_id_1=%s AND user_id_2=%s)", (user_a_id, user_b_id, user_b_id, user_a_id))
            row = cur.fetchone()
            if not row:
                print("Checking connection existence failed")
                exit(1)
            conn_id = row['connection_id']

        # 4. Accept Request
        success, msg = accept_request(conn_id, user_b_id)
        print(f"Accept Request (B): success={success}, msg={msg}")
        assert success

        # 5. Verify Connected
        res = search_users('Test B', user_a_id)
        status_a = res[0]['connection_status']
        print(f"Final Status (A->B): {status_a}")
        assert status_a == 'connected'

        print("ALL TESTS PASSED")

    finally:
        # cleanup
        conn.close()
