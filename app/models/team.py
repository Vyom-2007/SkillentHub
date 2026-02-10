from database.connection import get_db_connection

class Team:
    @staticmethod
    def create(name, event_name, created_by):
        conn = get_db_connection()
        if not conn: return False
        try:
            with conn.cursor() as cursor:
                # Create team
                sql = "INSERT INTO teams (team_name, event_name, created_by) VALUES (%s, %s, %s)"
                cursor.execute(sql, (name, event_name, created_by))
                team_id = cursor.lastrowid
                
                # Add creator as member (leader)
                sql_member = "INSERT INTO team_members (team_id, user_id, role) VALUES (%s, %s, 'leader')"
                cursor.execute(sql_member, (team_id, created_by))
                
            conn.commit()
            return team_id
        finally:
            conn.close()

    @staticmethod
    def get_by_id(team_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM teams WHERE team_id = %s", (team_id,))
                return cursor.fetchone()
        finally:
            conn.close()

    @staticmethod
    def get_user_teams(user_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT t.*, tm.role 
                    FROM teams t
                    JOIN team_members tm ON t.team_id = tm.team_id
                    WHERE tm.user_id = %s
                """
                cursor.execute(sql, (user_id,))
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def add_member(team_id, user_id, role='member'):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO team_members (team_id, user_id, role) VALUES (%s, %s, %s)"
                cursor.execute(sql, (team_id, user_id, role))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()

    @staticmethod
    def get_members(team_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT u.user_id, u.full_name, p.profile_picture, tm.role, tm.joined_at
                    FROM team_members tm
                    JOIN users u ON tm.user_id = u.user_id
                    LEFT JOIN profiles p ON u.user_id = p.user_id
                    WHERE tm.team_id = %s
                """
                cursor.execute(sql, (team_id,))
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def invite_member(team_id, inviter_id, email):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Find user by email
                cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                if not user: return 'user_not_found'
                
                invitee_id = user['user_id']
                
                # Check if already member
                cursor.execute("SELECT * FROM team_members WHERE team_id=%s AND user_id=%s", (team_id, invitee_id))
                if cursor.fetchone(): return 'already_member'

                # Create invitation
                sql = """
                    INSERT INTO team_invitations (team_id, inviter_id, invitee_id, status)
                    VALUES (%s, %s, %s, 'pending')
                """
                cursor.execute(sql, (team_id, inviter_id, invitee_id))
            conn.commit()
            return 'success'
        except Exception as e:
            print(e)
            return 'error'
        finally:
            conn.close()
