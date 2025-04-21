# --- START OF FILE database.py ---

import sqlite3
import os

DATABASE_NAME = 'prompts.db'

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def _add_column_if_not_exists(cursor, table_name, column_name, column_type, default_value=None):
    """Helper to add a column if it doesn't exist."""
    try:
        # Check if column exists
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [info['name'] for info in cursor.fetchall()]
        if column_name not in columns:
            print(f"Adding column '{column_name}' to table '{table_name}'...")
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            if default_value is not None:
                # Need to quote string defaults
                if isinstance(default_value, str):
                    alter_sql += f" DEFAULT '{default_value}'"
                else:
                    alter_sql += f" DEFAULT {default_value}"
            cursor.execute(alter_sql)
            print(f"Column '{column_name}' added successfully.")
        else:
             print(f"Column '{column_name}' already exists in '{table_name}'.")

    except sqlite3.OperationalError as e:
        # This specific error might occur if adding a column with default fails on older SQLite
        # but the PRAGMA check should prevent the ALTER attempt if column exists.
        print(f"Warning: Could not add or verify column '{column_name}' in '{table_name}': {e}")


def initialize_database():
    """Creates the database tables if they don't exist and adds missing columns."""
    conn = get_db_connection()
    cursor = conn.cursor()
    print("Initializing database and checking schema...")

    # Categories Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
            /* color and order_index added via ALTER below if needed */
        )
    ''')
    _add_column_if_not_exists(cursor, "categories", "color", "TEXT", default_value='#e0e0e0')
    _add_column_if_not_exists(cursor, "categories", "order_index", "INTEGER", default_value=0)
    cursor.execute("UPDATE categories SET order_index = id WHERE order_index IS NULL OR order_index = 0")


    # Sections Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
            /* color and order_index added via ALTER below if needed */
        )
    ''')
    # --- ADD THIS LINE for section color ---
    _add_column_if_not_exists(cursor, "sections", "color", "TEXT", default_value='#d0d0d0') # Slightly different default maybe?
    # --- END ADD ---
    _add_column_if_not_exists(cursor, "sections", "order_index", "INTEGER", default_value=0)
    cursor.execute("UPDATE sections SET order_index = id WHERE order_index IS NULL OR order_index = 0")


    # Prompts Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            content TEXT NOT NULL,
            section_id INTEGER NOT NULL,
            FOREIGN KEY (section_id) REFERENCES sections (id) ON DELETE CASCADE
            /* order_index added via ALTER below if needed */
        )
    ''')
    _add_column_if_not_exists(cursor, "prompts", "order_index", "INTEGER", default_value=0)
    cursor.execute("UPDATE prompts SET order_index = id WHERE order_index IS NULL OR order_index = 0")


    conn.commit()
    conn.close()
    print("Database initialized/schema checked successfully.")

# --- Helper to get next order index ---
def _get_next_order_index(cursor, table_name, parent_id_column=None, parent_id=None):
    query = f"SELECT MAX(order_index) FROM {table_name}"
    params = []
    if parent_id_column and parent_id is not None:
        query += f" WHERE {parent_id_column} = ?"
        params.append(parent_id)

    cursor.execute(query, params)
    max_index = cursor.fetchone()[0]
    return (max_index or 0) + 1

# --- Category Functions ---

def add_category(name, color='#e0e0e0'):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        next_order_index = _get_next_order_index(cursor, "categories")
        cursor.execute("INSERT INTO categories (name, color, order_index) VALUES (?, ?, ?)",
                       (name, color, next_order_index))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        print(f"Category '{name}' already exists.")
        return None
    finally:
        conn.close()

def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Order by the new column
    cursor.execute("SELECT * FROM categories ORDER BY order_index")
    categories = cursor.fetchall()
    conn.close()
    return categories

def update_category(category_id, name, color=None):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if color:
            cursor.execute("UPDATE categories SET name = ?, color = ? WHERE id = ?", (name, color, category_id))
        else:
            # Don't update color if not provided
             cursor.execute("UPDATE categories SET name = ? WHERE id = ?", (name, category_id))
        conn.commit()
    finally:
        conn.close()

def update_category_color(category_id, color):
     conn = get_db_connection()
     try:
         cursor = conn.cursor()
         cursor.execute("UPDATE categories SET color = ? WHERE id = ?", (color, category_id))
         conn.commit()
     finally:
         conn.close()

def delete_category(category_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit() # Cascading delete should handle sections and prompts
    finally:
        conn.close()

# --- Section Functions ---

def add_section(name, category_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        next_order_index = _get_next_order_index(cursor, "sections", "category_id", category_id)
        cursor.execute("INSERT INTO sections (name, category_id, order_index) VALUES (?, ?, ?)",
                       (name, category_id, next_order_index))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_sections(category_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Order by the new column
    cursor.execute("SELECT * FROM sections WHERE category_id = ? ORDER BY order_index", (category_id,))
    sections = cursor.fetchall()
    conn.close()
    return sections

def update_section(section_id, name):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE sections SET name = ? WHERE id = ?", (name, section_id))
        conn.commit()
    finally:
        conn.close()

# (After delete_section function)

def update_section_color(section_id, color):
     """Updates the color for a specific section."""
     conn = get_db_connection()
     try:
         cursor = conn.cursor()
         cursor.execute("UPDATE sections SET color = ? WHERE id = ?", (color, section_id))
         conn.commit()
         print(f"Updated color for section {section_id} to {color}")
     except Exception as e:
          print(f"Error updating color for section {section_id}: {e}")
     finally:
         conn.close()

def delete_section(section_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sections WHERE id = ?", (section_id,))
        conn.commit() # Cascading delete should handle prompts
    finally:
        conn.close()

# --- Prompt Functions ---

def add_prompt(title, description, content, section_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        next_order_index = _get_next_order_index(cursor, "prompts", "section_id", section_id)
        cursor.execute("INSERT INTO prompts (title, description, content, section_id, order_index) VALUES (?, ?, ?, ?, ?)",
                       (title, description, content, section_id, next_order_index))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_prompts(section_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Order by the new column
    cursor.execute("SELECT * FROM prompts WHERE section_id = ? ORDER BY order_index", (section_id,))
    prompts = cursor.fetchall()
    conn.close()
    return prompts

def get_prompt(prompt_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,))
    prompt = cursor.fetchone()
    conn.close()
    return prompt

def update_prompt(prompt_id, title, description, content):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE prompts SET title = ?, description = ?, content = ? WHERE id = ?",
                       (title, description, content, prompt_id))
        conn.commit()
    finally:
        conn.close()

def delete_prompt(prompt_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
        conn.commit()
    finally:
        conn.close()

def search_prompts_by_title(search_term):
    """Searches prompts by title and returns detailed info including category and section."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT
            p.id AS prompt_id,
            p.title AS prompt_title,
            p.description AS prompt_description,
            p.content AS prompt_content,
            s.name AS section_name,
            c.name AS category_name
        FROM prompts p
        JOIN sections s ON p.section_id = s.id
        JOIN categories c ON s.category_id = c.id
        WHERE p.title LIKE ?
        ORDER BY c.name, s.name, p.title -- Search results don't need custom order
    """
    like_term = f"%{search_term}%"
    cursor.execute(query, (like_term,))
    results = cursor.fetchall()
    conn.close()
    return results

# --- Reordering Functions ---

def _get_item_and_siblings(cursor, table_name, item_id, parent_id_column=None, parent_id=None):
    """Gets the item's order_index and the IDs/order_indices of its siblings."""
    where_clause = "1=1"
    params = []
    if parent_id_column and parent_id is not None:
        where_clause = f"{parent_id_column} = ?"
        params.append(parent_id)

    cursor.execute(f"SELECT id, order_index FROM {table_name} WHERE {where_clause} ORDER BY order_index", params)
    siblings = cursor.fetchall()

    current_item_index = -1
    current_order_index = -1
    for i, sibling in enumerate(siblings):
        if sibling['id'] == item_id:
            current_item_index = i
            current_order_index = sibling['order_index']
            break

    return siblings, current_item_index, current_order_index

def move_item(table_name, item_id, direction, parent_id_column=None, parent_id=None):
    """Moves an item up or down in the order_index within its siblings."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        siblings, current_item_index, current_order_index = _get_item_and_siblings(
            cursor, table_name, item_id, parent_id_column, parent_id
        )

        if current_item_index == -1:
            print(f"Error: Item {item_id} not found in {table_name} with parent {parent_id}")
            return False

        swap_with_index = -1
        if direction == "up" and current_item_index > 0:
            swap_with_index = current_item_index - 1
        elif direction == "down" and current_item_index < len(siblings) - 1:
            swap_with_index = current_item_index + 1
        else:
            print(f"Cannot move item {item_id} further {direction}.")
            return False # Cannot move further

        # Get the item to swap with
        swap_item = siblings[swap_with_index]
        swap_item_id = swap_item['id']
        swap_order_index = swap_item['order_index']

        # Perform the swap using a temporary high value to avoid unique constraint issues if any
        temp_index = 999999999 # A large temporary index
        cursor.execute(f"UPDATE {table_name} SET order_index = ? WHERE id = ?", (temp_index, item_id))
        cursor.execute(f"UPDATE {table_name} SET order_index = ? WHERE id = ?", (current_order_index, swap_item_id))
        cursor.execute(f"UPDATE {table_name} SET order_index = ? WHERE id = ?", (swap_order_index, item_id))

        conn.commit()
        print(f"Moved item {item_id} {direction} in {table_name}.")
        return True

    except Exception as e:
        print(f"Error moving item {item_id} in {table_name}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


# Initialize the database when the module is imported
if __name__ != "__main__": # Only run initialization if imported
    initialize_database()
elif __name__ == "__main__":
     # Allow running directly to initialize/check DB
     initialize_database()
     print("Database check/initialization complete (run directly).")
# --- END OF FILE database.py ---