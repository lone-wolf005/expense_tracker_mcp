import sqlite3
import json
import os
from typing import Optional

from fastmcp import FastMCP


mcp = FastMCP("Expense Tracker")

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Use absolute paths for database and categories files
DB_PATH = os.path.join(BASE_DIR, "database.db")
CATEGORIES_PATH = os.path.join(BASE_DIR, "categories.json")


def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Create and return a connection to the SQLite database.
    
    Args:
        db_path: Path to the SQLite database file (default: database.db)
    
    Returns:
        sqlite3.Connection: Database connection object
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Failed to connect to database: {e}")


def init_database(db_path: str = DB_PATH) -> None:
    """
    Initialize the database with required tables for expense tracking.
    
    Args:
        db_path: Path to the SQLite database file
    """
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # Create expenses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT,
                date TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        print(f"✓ Database initialized successfully at {db_path}")
        
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        raise sqlite3.Error(f"Database initialization failed: {e}")
    finally:
        if conn:
            conn.close()

def initialize_expense_database() -> str:
    """Initialize the expense tracker database with required tables."""
    try:
        init_database()
        return "Database initialized successfully with expenses and categories tables"
    except Exception as e:
        return f"Error initializing database: {str(e)}"


@mcp.resource("categories://list")
def get_categories_resource() -> str:
    """
    MCP Resource: Provides the list of available expense categories.
    Access this resource to see all valid categories and subcategories for expenses.
    """
    try:
        with open(CATEGORIES_PATH, 'r') as f:
            categories_data = json.load(f)
        
        result = "📂 Available Expense Categories\n"
        result += "=" * 70 + "\n\n"
        
        for category in categories_data.get('categories', []):
            result += f"{category['icon']} {category['name']} (ID: {category['id']})\n"
            if 'subcategories' in category:
                for subcat in category['subcategories']:
                    result += f"   └─ {subcat['name']} (ID: {subcat['id']})\n"
            result += "\n"
        
        return result
    except FileNotFoundError:
        return "Error: categories.json file not found"
    except json.JSONDecodeError:
        return "Error: Invalid JSON in categories.json"
    except Exception as e:
        return f"Error loading categories: {str(e)}"


@mcp.tool
def list_available_categories() -> str:
    """
    List all available expense categories and subcategories from categories.json.
    Use this to see valid category names when adding expenses.
    
    Returns:
        Formatted list of all categories with their subcategories
    """
    try:
        with open(CATEGORIES_PATH, 'r') as f:
            categories_data = json.load(f)
        
        result = "📂 Available Expense Categories\n"
        result += "=" * 70 + "\n\n"
        
        for category in categories_data.get('categories', []):
            result += f"{category['icon']} {category['name']} (ID: {category['id']})\n"
            if 'subcategories' in category:
                result += "   Subcategories:\n"
                for subcat in category['subcategories']:
                    result += f"   • {subcat['name']} (ID: {subcat['id']})\n"
            result += "\n"
        
        return result
    except FileNotFoundError:
        return "❌ Error: categories.json file not found"
    except json.JSONDecodeError:
        return "❌ Error: Invalid JSON in categories.json"
    except Exception as e:
        return f"❌ Error loading categories: {str(e)}"


@mcp.tool 
def add_expense(description: str, amount: float, category: str,) -> str:
    """Add an expense to the expense tracker database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO expenses (description, amount, category)
            VALUES (?,?,?)   """, (description, amount, category))
        conn.commit()
        return "Expense added successfully"
    except sqlite3.Error as e:
        return f"Error adding expense: {str(e)}"   
@mcp.tool
def list_all_expense() -> str:
    """List all expenses from the expense tracker database with their IDs."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses ORDER BY id")
        rows = cursor.fetchall()
        if rows:
            result = "📋 All Expenses:\n" + "="*60 + "\n"
            for row in rows:
                result += f"ID: {row['id']}\n"
                result += f"  Description: {row['description']}\n"
                result += f"  Amount: ${row['amount']:.2f}\n"
                result += f"  Category: {row['category'] or 'N/A'}\n"
                result += f"  Date: {row['date']}\n"
                result += "-"*60 + "\n"
            return result
        else:
            return "No expenses found"
    except sqlite3.Error as e:
        return f"Error listing expenses: {str(e)}"
    finally:
        if conn:
            conn.close()


@mcp.tool
def search_expense(search_term: str) -> str:
    """
    Search for expenses by description, category, or amount.
    Returns matching expenses with their IDs.
    
    Args:
        search_term: Text to search for in description or category
    
    Returns:
        Formatted list of matching expenses with IDs
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Search in description and category
        cursor.execute("""
            SELECT * FROM expenses
            WHERE description LIKE ? OR category LIKE ?
            ORDER BY id
        """, (f"%{search_term}%", f"%{search_term}%"))
        
        rows = cursor.fetchall()
        if rows:
            result = f"🔍 Search results for '{search_term}':\n" + "="*60 + "\n"
            for row in rows:
                result += f"ID: {row['id']}\n"
                result += f"  Description: {row['description']}\n"
                result += f"  Amount: ${row['amount']:.2f}\n"
                result += f"  Category: {row['category'] or 'N/A'}\n"
                result += f"  Date: {row['date']}\n"
                result += "-"*60 + "\n"
            return result
        else:
            return f"No expenses found matching '{search_term}'"
    except sqlite3.Error as e:
        return f"Error searching expenses: {str(e)}"
    finally:
        if conn:
            conn.close()

@mcp.tool
def get_expense_details_by_date_and_category(start_date: str, end_date: str, category: Optional[str] = None) -> str:
    """
    Get detailed list of expenses between two dates, optionally filtered by category.

    Args:
        start_date: The start date of the range (format: YYYY-MM-DD)
        end_date: The end date of the range (format: YYYY-MM-DD)
        category: The category to filter by (optional)

    Returns:
        Detailed list of expenses with all information
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query based on whether category is provided
        if category:
            cursor.execute("""
                SELECT * FROM expenses
                WHERE date BETWEEN ? AND ? AND category = ?
                ORDER BY date, id
            """, (start_date, end_date, category))
        else:
            cursor.execute("""
                SELECT * FROM expenses
                WHERE date BETWEEN ? AND ?
                ORDER BY date, id
            """, (start_date, end_date))
        
        rows = cursor.fetchall()

        if rows:
            if category:
                result = f"📋 Expenses in '{category}' ({start_date} to {end_date}):\n"
            else:
                result = f"📋 All Expenses ({start_date} to {end_date}):\n"
            result += "=" * 60 + "\n"
            
            for row in rows:
                result += f"ID: {row['id']}\n"
                result += f"  Date: {row['date']}\n"
                result += f"  Description: {row['description']}\n"
                result += f"  Category: {row['category'] or 'N/A'}\n"
                result += f"  Amount: ${row['amount']:.2f}\n"
                result += "-" * 60 + "\n"
            return result
        else:
            if category:
                return f"No expenses found in category '{category}' between {start_date} and {end_date}"
            else:
                return f"No expenses found between {start_date} and {end_date}"
    except sqlite3.Error as e:
        return f"Error retrieving expenses: {str(e)}"
    finally:
        if conn:
            conn.close()

@mcp.tool
def get_expense_summary_by_date_and_category(start_date: str, end_date: str, category: Optional[str] = None) -> str:
    """
    Get grouped summary of expenses between two dates, optionally filtered and grouped by category.
    
    If category is provided:
    - Filters expenses by that specific category
    - Groups results by category (showing only that category)
    
    If category is not provided:
    - Shows all expenses in the date range
    - Groups results by all categories found
    
    Args:
        start_date: The start date of the range (format: YYYY-MM-DD)
        end_date: The end date of the range (format: YYYY-MM-DD)
        category: The category to filter by (optional). If provided, only shows expenses from this category.
    
    Returns:
        Formatted summary with expenses grouped by category, showing totals
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query based on whether category is provided
        if category:
            # Filter by specific category
            cursor.execute("""
                SELECT category, date, description, amount
                FROM expenses
                WHERE date BETWEEN ? AND ? AND category = ?
                ORDER BY category, date
            """, (start_date, end_date, category))
        else:
            # Get all expenses in date range
            cursor.execute("""
                SELECT category, date, description, amount
                FROM expenses
                WHERE date BETWEEN ? AND ?
                ORDER BY category, date
            """, (start_date, end_date))
        
        rows = cursor.fetchall()
        
        if not rows:
            if category:
                return f"No expenses found in category '{category}' between {start_date} and {end_date}"
            else:
                return f"No expenses found between {start_date} and {end_date}"
        
        # Group expenses by category
        grouped_expenses = {}
        grand_total = 0.0
        
        for row in rows:
            cat = row['category'] or 'Uncategorized'
            if cat not in grouped_expenses:
                grouped_expenses[cat] = {
                    'expenses': [],
                    'total': 0.0
                }
            
            expense_data = {
                'date': row['date'],
                'description': row['description'],
                'amount': row['amount']
            }
            grouped_expenses[cat]['expenses'].append(expense_data)
            grouped_expenses[cat]['total'] += row['amount']
            grand_total += row['amount']
        
        # Format output
        result = f"📊 Expense Summary ({start_date} to {end_date})\n"
        result += "=" * 70 + "\n\n"
        
        for cat, data in sorted(grouped_expenses.items()):
            result += f"📁 Category: {cat}\n"
            result += f"   Total: ${data['total']:.2f}\n"
            result += "-" * 70 + "\n"
            
            for expense in data['expenses']:
                result += f"   • {expense['date']} | {expense['description']}: ${expense['amount']:.2f}\n"
            
            result += "\n"
        
        result += "=" * 70 + "\n"
        result += f"💰 GRAND TOTAL: ${grand_total:.2f}\n"
        result += f"📈 Categories: {len(grouped_expenses)}\n"
        result += f"📝 Total Expenses: {len(rows)}\n"
        
        return result
        
    except sqlite3.Error as e:
        return f"Error retrieving expenses: {str(e)}"
    finally:
        if conn:
            conn.close()

@mcp.tool
def get_expense_details(expense_id: int) -> str:
    """
    Get detailed information about a specific expense by ID.
    
    Args:
        expense_id: The ID of the expense to retrieve
    
    Returns:
        Detailed expense information
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        row = cursor.fetchone()
        
        if row:
            result = f"📄 Expense Details (ID: {row['id']}):\n" + "="*60 + "\n"
            result += f"Description: {row['description']}\n"
            result += f"Amount: ${row['amount']:.2f}\n"
            result += f"Category: {row['category'] or 'N/A'}\n"
            result += f"Date: {row['date']}\n"
            result += f"Created: {row['created_at']}\n"
            return result
        else:
            return f"❌ Expense with ID {expense_id} not found"
    except sqlite3.Error as e:
        return f"Error getting expense: {str(e)}"
    finally:
        if conn:
            conn.close()

@mcp.tool 
def delete_expense(description: str) -> str:  
    """Delete an expense from the expense tracker database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE description = ?", (description,))
        conn.commit()
        return "Expense deleted successfully"
    except sqlite3.Error as e:
        return f"Error deleting expense: {str(e)}"

@mcp.tool
def modify_expense(description: str, amount: float) -> str:
    """Modify an expense amount in the expense tracker database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE expenses SET amount = ? WHERE description = ?", (amount, description))
        conn.commit()
        return "Expense modified successfully"
    except sqlite3.Error as e:
        return f"Error modifying expense: {str(e)}"

if __name__ == "__main__":
    # Initialize database when running directly
    init_database()
    # Start MCP server
    mcp.run()
