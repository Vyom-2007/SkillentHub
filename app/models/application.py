from app.database.connection import get_db
from app.services.email_service import send_application_status_email

class Application:
    @staticmethod
    def create(data):
        db = get_db()
        cursor = db.cursor()
        try:
            # Check duplicate
            cursor.execute("""
                SELECT application_id FROM applications 
                WHERE user_id = %s AND item_type = %s AND item_id = %s
            """, (data['user_id'], data['item_type'], data['item_id']))
            if cursor.fetchone():
                return False # Duplicate
                
            fields = ['user_id', 'item_type', 'item_id', 'resume_path', 'cover_letter']
            cols = ', '.join(fields)
            placeholders = ', '.join(['%s'] * len(fields))
            values = [data.get(f) for f in fields]
            
            cursor.execute(f"INSERT INTO applications ({cols}) VALUES ({placeholders})", tuple(values))
            db.commit()
            return cursor.lastrowid
        except Exception as e:
            db.rollback()
            raise e
        finally:
            cursor.close()

    @staticmethod
    def update_status(application_id, status, job_title=None, user_email=None):
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("UPDATE applications SET status = %s WHERE application_id = %s", (status, application_id))
            db.commit()
            
            if status == 'accepted' and user_email:
                send_application_status_email(user_email, status, job_title or "Job")
                
            return True
        except Exception as e:
            db.rollback()
            raise e
        finally:
            cursor.close()

    @staticmethod
    def get_by_user(user_id):
        db = get_db()
        cursor = db.cursor()
        # Complex join to get item details (job/internship/comp)
        # For simplicity, we might do separate queries or a UNION?
        # Or just generic display and fetch details on demand. 
        # But list needs titles.
        # Let's do a UNION of jobs + internships + competitions + hackathons? Or just 4 queries in python.
        # Python merging is easier to maintain than massive union query.
        
        cursor.execute("SELECT * FROM applications WHERE user_id = %s ORDER BY applied_at DESC", (user_id,))
        apps = cursor.fetchall()
        
        # Hydrate with titles
        for app in apps:
            table = app['item_type'] + 's' # items table name
            id_col = app['item_type'] + '_id'
            cursor.execute(f"SELECT title FROM {table} WHERE {id_col} = %s", (app['item_id'],))
            res = cursor.fetchone()
            app['title'] = res['title'] if res else "Unknown"
            
        cursor.close()
        return apps
