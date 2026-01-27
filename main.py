import json
import os
from typing import Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables
load_dotenv()

mcp = FastMCP("Expense Tracker")

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATEGORIES_PATH = os.path.join(BASE_DIR, "categories.json")

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/expense_tracker")


def get_db_connection():
    """
    Create and return a connection to the MongoDB database.
    
    Returns:
        MongoDB database object
    """
    try:
        client = MongoClient(MONGODB_URL)
        # Test the connection
        client.admin.command('ping')
        db = client.get_database()
        return db
    except PyMongoError as e:
        raise PyMongoError(f"Failed to connect to MongoDB: {e}")


def init_database() -> None:
    """
    Initialize the MongoDB database with required collections and indexes.
    """
    try:
        db = get_db_connection()
        
        # Create expenses collection if it doesn't exist
        if "expenses" not in db.list_collection_names():
            db.create_collection("expenses")
        
        # Create indexes for better query performance
        expenses_collection = db["expenses"]
        expenses_collection.create_index("date")
        expenses_collection.create_index("category")
        expenses_collection.create_index("description")
        
        print(f"✓ MongoDB database initialized successfully")
        
    except PyMongoError as e:
        raise PyMongoError(f"Database initialization failed: {e}")


def initialize_expense_database() -> str:
    """Initialize the expense tracker database with required collections."""
    try:
        init_database()
        return "Database initialized successfully with expenses collection"
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
def add_expense(description: str, amount: float, category: str) -> str:
    """Add an expense to the expense tracker database."""
    try:
        db = get_db_connection()
        expenses_collection = db["expenses"]
        
        expense_doc = {
            "description": description,
            "amount": amount,
            "category": category,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "created_at": datetime.now()
        }
        
        result = expenses_collection.insert_one(expense_doc)
        return f"✓ Expense added successfully with ID: {result.inserted_id}"
    except PyMongoError as e:
        return f"❌ Error adding expense: {str(e)}"


@mcp.tool
def list_all_expense() -> str:
    """List all expenses from the expense tracker database with their IDs."""
    try:
        db = get_db_connection()
        expenses_collection = db["expenses"]
        
        expenses = list(expenses_collection.find().sort("_id", 1))
        
        if expenses:
            result = "📋 All Expenses:\n" + "="*60 + "\n"
            for expense in expenses:
                result += f"ID: {expense['_id']}\n"
                result += f"  Description: {expense['description']}\n"
                result += f"  Amount: ${expense['amount']:.2f}\n"
                result += f"  Category: {expense.get('category', 'N/A')}\n"
                result += f"  Date: {expense['date']}\n"
                result += "-"*60 + "\n"
            return result
        else:
            return "No expenses found"
    except PyMongoError as e:
        return f"❌ Error listing expenses: {str(e)}"


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
        db = get_db_connection()
        expenses_collection = db["expenses"]
        
        # Search in description and category using regex
        query = {
            "$or": [
                {"description": {"$regex": search_term, "$options": "i"}},
                {"category": {"$regex": search_term, "$options": "i"}}
            ]
        }
        
        expenses = list(expenses_collection.find(query).sort("_id", 1))
        
        if expenses:
            result = f"🔍 Search results for '{search_term}':\n" + "="*60 + "\n"
            for expense in expenses:
                result += f"ID: {expense['_id']}\n"
                result += f"  Description: {expense['description']}\n"
                result += f"  Amount: ${expense['amount']:.2f}\n"
                result += f"  Category: {expense.get('category', 'N/A')}\n"
                result += f"  Date: {expense['date']}\n"
                result += "-"*60 + "\n"
            return result
        else:
            return f"No expenses found matching '{search_term}'"
    except PyMongoError as e:
        return f"❌ Error searching expenses: {str(e)}"


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
        db = get_db_connection()
        expenses_collection = db["expenses"]
        
        # Build query based on whether category is provided
        query: dict = {
            "date": {"$gte": start_date, "$lte": end_date}
        }
        
        if category:
            query["category"] = category
        
        expenses = list(expenses_collection.find(query).sort([("date", 1), ("_id", 1)]))

        if expenses:
            if category:
                result = f"📋 Expenses in '{category}' ({start_date} to {end_date}):\n"
            else:
                result = f"📋 All Expenses ({start_date} to {end_date}):\n"
            result += "=" * 60 + "\n"
            
            for expense in expenses:
                result += f"ID: {expense['_id']}\n"
                result += f"  Date: {expense['date']}\n"
                result += f"  Description: {expense['description']}\n"
                result += f"  Category: {expense.get('category', 'N/A')}\n"
                result += f"  Amount: ${expense['amount']:.2f}\n"
                result += "-" * 60 + "\n"
            return result
        else:
            if category:
                return f"No expenses found in category '{category}' between {start_date} and {end_date}"
            else:
                return f"No expenses found between {start_date} and {end_date}"
    except PyMongoError as e:
        return f"❌ Error retrieving expenses: {str(e)}"


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
        db = get_db_connection()
        expenses_collection = db["expenses"]
        
        # Build query based on whether category is provided
        query: dict = {
            "date": {"$gte": start_date, "$lte": end_date}
        }
        
        if category:
            query["category"] = category
        
        expenses = list(expenses_collection.find(query).sort([("category", 1), ("date", 1)]))
        
        if not expenses:
            if category:
                return f"No expenses found in category '{category}' between {start_date} and {end_date}"
            else:
                return f"No expenses found between {start_date} and {end_date}"
        
        # Group expenses by category
        grouped_expenses = {}
        grand_total = 0.0
        
        for expense in expenses:
            cat = expense.get('category', 'Uncategorized')
            if cat not in grouped_expenses:
                grouped_expenses[cat] = {
                    'expenses': [],
                    'total': 0.0
                }
            
            expense_data = {
                'date': expense['date'],
                'description': expense['description'],
                'amount': expense['amount']
            }
            grouped_expenses[cat]['expenses'].append(expense_data)
            grouped_expenses[cat]['total'] += expense['amount']
            grand_total += expense['amount']
        
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
        result += f"📝 Total Expenses: {len(expenses)}\n"
        
        return result
        
    except PyMongoError as e:
        return f"❌ Error retrieving expenses: {str(e)}"


@mcp.tool
def get_expense_details(expense_id: str) -> str:
    """
    Get detailed information about a specific expense by ID.
    
    Args:
        expense_id: The MongoDB ObjectId of the expense to retrieve (as string)
    
    Returns:
        Detailed expense information
    """
    try:
        from bson import ObjectId
        db = get_db_connection()
        expenses_collection = db["expenses"]
        
        expense = expenses_collection.find_one({"_id": ObjectId(expense_id)})
        
        if expense:
            result = f"📄 Expense Details (ID: {expense['_id']}):\n" + "="*60 + "\n"
            result += f"Description: {expense['description']}\n"
            result += f"Amount: ${expense['amount']:.2f}\n"
            result += f"Category: {expense.get('category', 'N/A')}\n"
            result += f"Date: {expense['date']}\n"
            result += f"Created: {expense['created_at']}\n"
            return result
        else:
            return f"❌ Expense with ID {expense_id} not found"
    except Exception as e:
        return f"❌ Error getting expense: {str(e)}"


@mcp.tool
def delete_expense(description: str) -> str:
    """Delete an expense from the expense tracker database by description."""
    try:
        db = get_db_connection()
        expenses_collection = db["expenses"]
        
        result = expenses_collection.delete_many({"description": description})
        
        if result.deleted_count > 0:
            return f"✓ Deleted {result.deleted_count} expense(s) successfully"
        else:
            return f"❌ No expenses found with description '{description}'"
    except PyMongoError as e:
        return f"❌ Error deleting expense: {str(e)}"


@mcp.tool
def modify_expense(description: str, amount: float) -> str:
    """Modify an expense amount in the expense tracker database."""
    try:
        db = get_db_connection()
        expenses_collection = db["expenses"]
        
        result = expenses_collection.update_many(
            {"description": description},
            {"$set": {"amount": amount}}
        )
        
        if result.modified_count > 0:
            return f"✓ Modified {result.modified_count} expense(s) successfully"
        else:
            return f"❌ No expenses found with description '{description}'"
    except PyMongoError as e:
        return f"❌ Error modifying expense: {str(e)}"


if __name__ == "__main__":
    # Initialize database when running directly
    init_database()
    # Start MCP server
    mcp.run()

# Made with Bob
