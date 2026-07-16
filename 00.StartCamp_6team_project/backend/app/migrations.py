"""Small idempotent migrations for the project's existing SQLite database.

SQLAlchemy's create_all creates new tables but never adds columns to tables that
already exist. These additive statements preserve all legacy community rows and
avoid rebuilding the 6,500+ row content database.
"""

from sqlalchemy.engine import Engine


def _columns(connection, table_name: str) -> set[str]:
    rows = connection.exec_driver_sql(f'PRAGMA table_info("{table_name}")')
    return {str(row[1]) for row in rows}


def migrate_auth_ownership(engine: Engine) -> None:
    """Add nullable ownership columns required by account-based community data."""
    with engine.begin() as connection:
        post_columns = _columns(connection, "posts")
        if post_columns and "author_id" not in post_columns:
            connection.exec_driver_sql(
                "ALTER TABLE posts ADD COLUMN author_id INTEGER "
                "REFERENCES users(id) ON DELETE SET NULL"
            )

        comment_columns = _columns(connection, "comments")
        if comment_columns and "author_id" not in comment_columns:
            connection.exec_driver_sql(
                "ALTER TABLE comments ADD COLUMN author_id INTEGER "
                "REFERENCES users(id) ON DELETE SET NULL"
            )

        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_posts_author_id ON posts (author_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_comments_author_id ON comments (author_id)"
        )


def migrate_community_courses(engine: Engine) -> None:
    """Add course-style travel posts without rebuilding existing review data."""
    with engine.begin() as connection:
        post_columns = _columns(connection, "posts")
        if post_columns and "post_type" not in post_columns:
            connection.exec_driver_sql(
                "ALTER TABLE posts ADD COLUMN post_type VARCHAR(16) "
                "NOT NULL DEFAULT 'review'"
            )
        if post_columns and "travel_date" not in post_columns:
            connection.exec_driver_sql("ALTER TABLE posts ADD COLUMN travel_date DATE")

        connection.exec_driver_sql(
            "CREATE TABLE IF NOT EXISTS post_course_items ("
            "id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, "
            "post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE, "
            "content_id VARCHAR(32) NOT NULL REFERENCES tour_contents(contentid), "
            "sort_order INTEGER NOT NULL DEFAULT 0, "
            "CONSTRAINT uq_post_course_items_order UNIQUE (post_id, sort_order)"
            ")"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_posts_post_type ON posts (post_type)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_posts_travel_date ON posts (travel_date)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_post_course_items_post_id "
            "ON post_course_items (post_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_post_course_items_content_id "
            "ON post_course_items (content_id)"
        )
