import psycopg2
from psycopg2 import sql


class TgMessage:
    def __init__(self, user_id: int, dialog_id: int, dialog_name: str, message_text: str, message: dict):
        self.user_id = user_id
        self.dialog_id = dialog_id
        self.dialog_name = dialog_name
        self.message_text = message_text
        self.message = message

    def to_str(self):
        return f"TgMessage(user_id={self.user_id}, dialog_id={self.dialog_id}, dialog_name='{self.dialog_name}', message_text='{self.message_text}', message={self.message})"


class PostgresStorage:
    def __init__(self, db_name="messages_db", user="postgres", password="password", host="localhost", port="5499"):
        self.conn = psycopg2.connect(dbname=db_name, user=user, password=password, host=host, port=port)
        self._initialize_tables()

    def _initialize_tables(self):
        with self.conn.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS peer (
                    id BIGINT PRIMARY KEY,
                    title TEXT,
                    username TEXT,
                    peer_type TEXT,
                    users_count INTEGER DEFAULT 0,
                    data JSONB,
                    full_chat_data JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE TABLE IF NOT EXISTS message (
                    id BIGINT,
                    user_id BIGINT,
                    dialog_id BIGINT,
                    dialog_name TEXT,
                    message_text TEXT,
                    message JSONB,
                    deleted BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    primary key (id, dialog_id)
                );
                
                create table if not exists user_dialog (
                    dialog_id BIGINT,
                    user_id BIGINT,
                    processed boolean default false,
                    primary key (dialog_id, user_id)
                );
            ''')
            self.conn.commit()

    def store_messages(self, messages):
        with self.conn.cursor() as cursor:
            for message in messages:
                cursor.execute('''
                    INSERT INTO message (id, user_id, dialog_id, dialog_name, message, message_text)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT ON CONSTRAINT message_pkey DO UPDATE SET
                        user_id = EXCLUDED.user_id,
                        dialog_id = EXCLUDED.dialog_id,
                        dialog_name = EXCLUDED.dialog_name,
                        message_text = EXCLUDED.message_text,
                        message = EXCLUDED.message,
                        deleted = EXCLUDED.deleted;
                ''', (
                    message['id'], message['user_id'], message['dialog_id'], message['dialog_name'], message['message'],
                    message['message_text']))
            self.conn.commit()

    def store_peer(self, peers):
        with self.conn.cursor() as cursor:
            for user in peers:
                cursor.execute('''
                    INSERT INTO peer (id, title, username, peer_type, data, users_count)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        username = EXCLUDED.username,
                        title = EXCLUDED.title,
                        users_count = EXCLUDED.users_count,
                        peer_type = EXCLUDED.peer_type,
                        data = EXCLUDED.data,
                        full_chat_data = EXCLUDED.full_chat_data;
                ''', (
                    user['id'], user['title'], user['username'], user['peer_type'], user['data'], user['users_count']))
            self.conn.commit()

    def store_full_chat_data(self, peer_id, full_chat_data):
        with self.conn.cursor() as cursor:
            cursor.execute('''
                UPDATE peer SET full_chat_data = %s WHERE id = %s;
            ''', (full_chat_data, peer_id))
            self.conn.commit()

    def store_users_count(self, peer_id, users_count):
        with self.conn.cursor() as cursor:
            cursor.execute('''
                UPDATE peer SET users_count = %s WHERE id = %s;
            ''', (users_count, peer_id))
            self.conn.commit()

    def store_user_dialog(self, dialog_id, user_id):
        with self.conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO user_dialog (user_id, dialog_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;
            ''', (user_id, dialog_id))
            self.conn.commit()

    def mark_dialog_processed(self, dialog_id, user_id):
        with self.conn.cursor() as cursor:
            cursor.execute('''
                update user_dialog set processed = true where dialog_id = %s and user_id = %s;
            ''', (dialog_id, user_id))
            self.conn.commit()

    def get_is_dialog_processed(self, dialog_id, user_id):
        with self.conn.cursor() as cursor:
            cursor.execute('''
                SELECT count(*) FROM user_dialog WHERE dialog_id = %s and user_id = %s and processed = true;
            ''', (dialog_id, user_id))
            return cursor.fetchone()[0] == 1

    def mark_message_deleted(self, message_id, dialog_id):
        with self.conn.cursor() as cursor:
            cursor.execute('''
                UPDATE message SET deleted = true WHERE id = %s and dialog_id = %s;
            ''', (message_id, dialog_id,))
            self.conn.commit()

    def search_peer(self, id):
        with self.conn.cursor() as cursor:
            cursor.execute('''
                SELECT * FROM peer WHERE id = %s;
            ''', (id,))
            return cursor.fetchone()

    def search_messages(self, query, field="dialog_name"):
        with self.conn.cursor() as cursor:
            cursor.execute(sql.SQL('''
                SELECT * FROM message WHERE {} ILIKE %s;
            ''').format(sql.Identifier(field)), (f'%{query}%',))
            return cursor.fetchall()

    def count_messages(self, user_id):
        with self.conn.cursor() as cursor:
            cursor.execute('''
                SELECT count(*) FROM message WHERE user_id = %s and deleted = false;
            ''', (user_id,))
            return cursor.fetchone()[0]


    def load_messages_in_batches(self, user_id, batch_size=1000) -> list[TgMessage]:
        with self.conn.cursor(name='message_cursor') as cursor:
            cursor.itersize = batch_size
            cursor.execute('''
            SELECT user_id, dialog_id, dialog_name, message_text, message
            FROM message
            WHERE user_id = %s AND deleted = false;
        ''', (user_id,))
            for row in cursor:
                yield TgMessage(user_id=row[0], dialog_id=row[1], dialog_name=row[2], message_text=row[3],
                                message=row[4])

    def close_connection(self):
        self.conn.close()
