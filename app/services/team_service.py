"""
Team service.
Handles team creation, invitations, member management, and team registration.
"""
from app.database.connection import execute_query, execute_insert, execute_update, get_db_connection
from app.services import notification_service, connection_service


def create_team(user_id, team_name, item_type, item_id, max_members=None):
    """Create a new team and add creator as leader."""
    # Check if user already has a team for this event
    existing = get_user_team_for_event(user_id, item_type, item_id)
    if existing:
        return None, "You are already in a team for this event"
    
    # Get max members from event if not specified
    if max_members is None:
        max_members = get_event_max_team_size(item_type, item_id)
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Insert team
            team_query = """
                INSERT INTO teams (team_name, item_type, item_id, created_by, max_members)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(team_query, (team_name, item_type, item_id, user_id, max_members))
            team_id = cursor.lastrowid
            
            # Insert creator as leader
            member_query = """
                INSERT INTO team_members (team_id, user_id, role)
                VALUES (%s, %s, 'leader')
            """
            cursor.execute(member_query, (team_id, user_id))
        
        connection.commit()
        return team_id, None
    except Exception as e:
        connection.rollback()
        return None, str(e)
    finally:
        connection.close()


def invite_member(leader_id, team_id, target_user_id):
    """Invite a connected user to the team."""
    # Verify leader owns team
    team = get_team_by_id(team_id)
    if not team:
        return False, "Team not found"
    if team['created_by'] != leader_id:
        return False, "Only team leader can invite members"
    
    if target_user_id == leader_id:
        return False, "Cannot invite yourself"
    
    # Verify connection exists
    if not connection_service.are_connected(leader_id, target_user_id):
        return False, "You can only invite users you are connected with"
    
    # Verify target not already in team for this event
    existing_team = get_user_team_for_event(target_user_id, team['item_type'], team['item_id'])
    if existing_team:
        return False, "User is already in a team for this event"
    
    # Check if already invited
    existing_invite = get_pending_invitation(team_id, target_user_id)
    if existing_invite:
        return False, "User already has a pending invitation"
    
    # Check max members
    member_count = get_team_member_count(team_id)
    pending_count = get_pending_invitation_count(team_id)
    if team['max_members'] and (member_count + pending_count) >= team['max_members']:
        return False, "Team is at maximum capacity"
    
    # Insert invitation
    query = """
        INSERT INTO team_invitations (team_id, invited_user_id, invited_by, status)
        VALUES (%s, %s, %s, 'pending')
    """
    inv_id = execute_insert(query, (team_id, target_user_id, leader_id))
    
    if inv_id:
        # Create notification
        create_team_notification(target_user_id, leader_id, team, 'team_invitation')
        return True, inv_id
    return False, "Failed to send invitation"


def accept_invitation(user_id, invitation_id):
    """Accept a team invitation."""
    invitation = get_invitation_by_id(invitation_id)
    if not invitation:
        return False, "Invitation not found"
    
    if invitation['invited_user_id'] != user_id:
        return False, "Not authorized"
    
    if invitation['status'] != 'pending':
        return False, "Invitation already processed"
    
    team = get_team_by_id(invitation['team_id'])
    if not team:
        return False, "Team no longer exists"
    
    # Check if user is already in another team for this event
    existing_team = get_user_team_for_event(user_id, team['item_type'], team['item_id'])
    if existing_team:
        return False, "You are already in a team for this event"
    
    # Check max members again
    member_count = get_team_member_count(invitation['team_id'])
    if team['max_members'] and member_count >= team['max_members']:
        return False, "Team is now full"
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Update invitation
            cursor.execute("""
                UPDATE team_invitations 
                SET status = 'accepted', responded_at = CURRENT_TIMESTAMP
                WHERE invitation_id = %s
            """, (invitation_id,))
            
            # Add to team
            cursor.execute("""
                INSERT INTO team_members (team_id, user_id, role)
                VALUES (%s, %s, 'member')
            """, (invitation['team_id'], user_id))
        
        connection.commit()
        
        # Notify leader
        create_team_notification(team['created_by'], user_id, team, 'team_invitation_accepted')
        
        return True, "Joined team successfully"
    except Exception as e:
        connection.rollback()
        return False, str(e)
    finally:
        connection.close()


def reject_invitation(user_id, invitation_id):
    """Reject a team invitation."""
    invitation = get_invitation_by_id(invitation_id)
    if not invitation:
        return False, "Invitation not found"
    
    if invitation['invited_user_id'] != user_id:
        return False, "Not authorized"
    
    if invitation['status'] != 'pending':
        return False, "Invitation already processed"
    
    query = """
        UPDATE team_invitations 
        SET status = 'rejected', responded_at = CURRENT_TIMESTAMP
        WHERE invitation_id = %s
    """
    execute_update(query, (invitation_id,))
    
    return True, "Invitation declined"


def leave_team(user_id, team_id):
    """Leave a team (members only, leader cannot leave)."""
    member = get_team_member(team_id, user_id)
    if not member:
        return False, "You are not in this team"
    
    if member['role'] == 'leader':
        return False, "Leader cannot leave the team. Transfer leadership or delete the team."
    
    query = "DELETE FROM team_members WHERE team_id = %s AND user_id = %s"
    execute_update(query, (team_id, user_id))
    
    return True, "Left team successfully"


def remove_member(leader_id, team_id, target_user_id):
    """Remove a member from team (leader only)."""
    team = get_team_by_id(team_id)
    if not team or team['created_by'] != leader_id:
        return False, "Not authorized"
    
    if target_user_id == leader_id:
        return False, "Cannot remove yourself"
    
    member = get_team_member(team_id, target_user_id)
    if not member:
        return False, "User is not in this team"
    
    query = "DELETE FROM team_members WHERE team_id = %s AND user_id = %s"
    execute_update(query, (team_id, target_user_id))
    
    return True, "Member removed"


def register_team_for_event(leader_id, team_id):
    """Register entire team for the event (transactional)."""
    team = get_team_by_id(team_id)
    if not team:
        return False, "Team not found"
    
    if team['created_by'] != leader_id:
        return False, "Only team leader can register the team"
    
    # Get min/max from event
    min_size, max_size = get_event_team_constraints(team['item_type'], team['item_id'])
    
    # Get members
    members = get_team_members(team_id)
    member_count = len(members)
    
    if min_size and member_count < min_size:
        return False, f"Team needs at least {min_size} members"
    if max_size and member_count > max_size:
        return False, f"Team cannot exceed {max_size} members"
    
    # Check if team already registered
    existing = execute_query(
        "SELECT 1 FROM applications WHERE team_id = %s LIMIT 1",
        (team_id,), fetch_one=True
    )
    if existing:
        return False, "Team is already registered"
    
    # Transaction: Insert applications for all members
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            for member in members:
                cursor.execute("""
                    INSERT INTO applications (user_id, item_type, item_id, team_id, status)
                    VALUES (%s, %s, %s, %s, 'applied')
                """, (member['user_id'], team['item_type'], team['item_id'], team_id))
        
        connection.commit()
        return True, "Team registered successfully"
    except Exception as e:
        connection.rollback()
        return False, str(e)
    finally:
        connection.close()


# ========== HELPER FUNCTIONS ==========

def get_team_by_id(team_id):
    """Get team by ID."""
    query = "SELECT * FROM teams WHERE team_id = %s"
    return execute_query(query, (team_id,), fetch_one=True)


def get_user_team_for_event(user_id, item_type, item_id):
    """Check if user is in a team for this event."""
    query = """
        SELECT t.* FROM teams t
        JOIN team_members tm ON t.team_id = tm.team_id
        WHERE tm.user_id = %s AND t.item_type = %s AND t.item_id = %s
    """
    return execute_query(query, (user_id, item_type, item_id), fetch_one=True)


def get_team_members(team_id):
    """Get all members of a team."""
    query = """
        SELECT tm.*, p.full_name, p.profile_picture, p.headline
        FROM team_members tm
        JOIN profiles p ON tm.user_id = p.user_id
        WHERE tm.team_id = %s
        ORDER BY tm.role DESC, tm.joined_at ASC
    """
    return execute_query(query, (team_id,), fetch_all=True) or []


def get_team_member(team_id, user_id):
    """Get specific team member."""
    query = "SELECT * FROM team_members WHERE team_id = %s AND user_id = %s"
    return execute_query(query, (team_id, user_id), fetch_one=True)


def get_team_member_count(team_id):
    """Count team members."""
    result = execute_query(
        "SELECT COUNT(*) as count FROM team_members WHERE team_id = %s",
        (team_id,), fetch_one=True
    )
    return result['count'] if result else 0


def get_pending_invitation_count(team_id):
    """Count pending invitations."""
    result = execute_query(
        "SELECT COUNT(*) as count FROM team_invitations WHERE team_id = %s AND status = 'pending'",
        (team_id,), fetch_one=True
    )
    return result['count'] if result else 0


def get_pending_invitation(team_id, user_id):
    """Get pending invitation for user."""
    query = """
        SELECT * FROM team_invitations 
        WHERE team_id = %s AND invited_user_id = %s AND status = 'pending'
    """
    return execute_query(query, (team_id, user_id), fetch_one=True)


def get_invitation_by_id(invitation_id):
    """Get invitation by ID."""
    query = "SELECT * FROM team_invitations WHERE invitation_id = %s"
    return execute_query(query, (invitation_id,), fetch_one=True)


def get_user_invitations(user_id):
    """Get pending invitations for user."""
    query = """
        SELECT ti.*, t.team_name, t.item_type, t.item_id,
               p.full_name as invited_by_name, p.profile_picture as invited_by_picture
        FROM team_invitations ti
        JOIN teams t ON ti.team_id = t.team_id
        JOIN profiles p ON ti.invited_by = p.user_id
        WHERE ti.invited_user_id = %s AND ti.status = 'pending'
        ORDER BY ti.invited_at DESC
    """
    return execute_query(query, (user_id,), fetch_all=True) or []


def get_my_teams(user_id):
    """Get all teams user is a member of."""
    query = """
        SELECT t.*, tm.role,
               (SELECT COUNT(*) FROM team_members WHERE team_id = t.team_id) as member_count
        FROM teams t
        JOIN team_members tm ON t.team_id = tm.team_id
        WHERE tm.user_id = %s AND t.is_active = 1
        ORDER BY t.created_at DESC
    """
    return execute_query(query, (user_id,), fetch_all=True) or []


def get_team_details(team_id):
    """Get full team details with members and pending invitations."""
    team = get_team_by_id(team_id)
    if not team:
        return None
    
    team['members'] = get_team_members(team_id)
    team['pending_invitations'] = execute_query(
        """SELECT ti.*, p.full_name, p.profile_picture
           FROM team_invitations ti
           JOIN profiles p ON ti.invited_user_id = p.user_id
           WHERE ti.team_id = %s AND ti.status = 'pending'""",
        (team_id,), fetch_all=True
    ) or []
    
    # Check registration status
    team['is_registered'] = bool(execute_query(
        "SELECT 1 FROM applications WHERE team_id = %s LIMIT 1",
        (team_id,), fetch_one=True
    ))
    
    return team


def get_event_max_team_size(item_type, item_id):
    """Get max team size from event."""
    table = 'competitions' if item_type == 'competition' else 'hackathons'
    id_col = 'competition_id' if item_type == 'competition' else 'hackathon_id'
    query = f"SELECT team_size_max FROM {table} WHERE {id_col} = %s"
    result = execute_query(query, (item_id,), fetch_one=True)
    return result.get('team_size_max') if result else None


def get_event_team_constraints(item_type, item_id):
    """Get min/max team size from event."""
    table = 'competitions' if item_type == 'competition' else 'hackathons'
    id_col = 'competition_id' if item_type == 'competition' else 'hackathon_id'
    query = f"SELECT team_size_min, team_size_max FROM {table} WHERE {id_col} = %s"
    result = execute_query(query, (item_id,), fetch_one=True)
    if result:
        return result.get('team_size_min'), result.get('team_size_max')
    return None, None


def get_connectable_users(user_id, team_id):
    """Get connected users who can be invited."""
    team = get_team_by_id(team_id)
    if not team:
        return []
    
    query = """
        SELECT p.user_id, p.full_name, p.headline, p.profile_picture
        FROM connections c
        JOIN profiles p ON p.user_id = CASE 
            WHEN c.user_id_1 = %s THEN c.user_id_2 
            ELSE c.user_id_1 
        END
        WHERE (c.user_id_1 = %s OR c.user_id_2 = %s) 
          AND c.status = 'accepted'
          AND p.user_id NOT IN (
              SELECT user_id FROM team_members WHERE team_id = %s
          )
          AND p.user_id NOT IN (
              SELECT invited_user_id FROM team_invitations 
              WHERE team_id = %s AND status = 'pending'
          )
          AND p.user_id NOT IN (
              SELECT tm.user_id FROM team_members tm
              JOIN teams t ON tm.team_id = t.team_id
              WHERE t.item_type = %s AND t.item_id = %s
          )
    """
    return execute_query(query, (
        user_id, user_id, user_id, team_id, team_id, 
        team['item_type'], team['item_id']
    ), fetch_all=True) or []


def create_team_notification(to_user_id, from_user_id, team, notif_type):
    """Create notification for team events."""
    sender_query = "SELECT full_name FROM profiles WHERE user_id = %s"
    sender = execute_query(sender_query, (from_user_id,), fetch_one=True)
    sender_name = sender['full_name'] if sender else 'Someone'
    
    if notif_type == 'team_invitation':
        content = f"{sender_name} invited you to join team '{team['team_name']}'"
    elif notif_type == 'team_invitation_accepted':
        content = f"{sender_name} joined your team '{team['team_name']}'"
    else:
        content = f"Team update for '{team['team_name']}'"
    
    notification_service.create_notification(to_user_id, notif_type, content, team['team_id'])
