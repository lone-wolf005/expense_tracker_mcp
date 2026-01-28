import json
import os
from typing import Optional
from datetime import datetime, timedelta
import hashlib
import secrets
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
from fastmcp import FastMCP
from bson import ObjectId

# Load environment variables
load_dotenv()

mcp = FastMCP("Expense Tracker")

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATEGORIES_PATH = os.path.join(BASE_DIR, "categories.json")

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/expense_tracker")

# Session configuration - Token expires after 24 hours by default
SESSION_TIMEOUT_HOURS = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))


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


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_session_token() -> str:
    """Generate a secure random session token."""
    return secrets.token_urlsafe(32)


def init_database() -> None:
    """
    Initialize the MongoDB database with required collections and indexes.
    """
    try:
        db = get_db_connection()
        
        # Create users collection if it doesn't exist
        if "users" not in db.list_collection_names():
            db.create_collection("users")
        
        # Create expenses collection if it doesn't exist
        if "expenses" not in db.list_collection_names():
            db.create_collection("expenses")
        
        # Create indexes for users collection
        users_collection = db["users"]
        users_collection.create_index("username", unique=True)
        users_collection.create_index("email", unique=True)
        users_collection.create_index("session_token")
        users_collection.create_index("session_expires_at")
        
        # Create indexes for expenses collection
        expenses_collection = db["expenses"]
        expenses_collection.create_index("user_id")
        expenses_collection.create_index("date")
        expenses_collection.create_index("category")
        expenses_collection.create_index("description")
        expenses_collection.create_index([("user_id", 1), ("date", -1)])
        
        print(f"✓ MongoDB database initialized successfully")
        
    except PyMongoError as e:
        raise PyMongoError(f"Database initialization failed: {e}")


def initialize_expense_database() -> str:
    """Initialize the expense tracker database with required collections."""
    try:
        init_database()
        return "Database initialized successfully with users and expenses collections"
    except Exception as e:
        return f"Error initializing database: {str(e)}"


@mcp.tool
def register_user(username: str, email: str, password: str) -> str:
    """
    Register a new user in the system.
    
    Args:
        username: Unique username for the user
        email: User's email address (must be unique)
        password: User's password (will be hashed)
    
    Returns:
        Success message with user_id or error message
    """
    try:
        db = get_db_connection()
        users_collection = db["users"]
        
        # Check if username or email already exists
        if users_collection.find_one({"username": username}):
            return f"❌ Username '{username}' already exists"
        
        if users_collection.find_one({"email": email}):
            return f"❌ Email '{email}' already registered"
        
        # Create user document
        user_doc = {
            "username": username,
            "email": email,
            "password_hash": hash_password(password),
            "created_at": datetime.now(),
            "session_token": None,
            "session_expires_at": None
        }
        
        result = users_collection.insert_one(user_doc)
        return f"✓ User registered successfully! User ID: {result.inserted_id}"
    except PyMongoError as e:
        return f"❌ Error registering user: {str(e)}"


@mcp.tool
def login_user(username: str, password: str) -> str:
    """
    Login a user and generate a session token.
    
    Args:
        username: Username or email
        password: User's password
    
    Returns:
        Success message with session token or error message
    """
    try:
        db = get_db_connection()
        users_collection = db["users"]
        
        # Find user by username or email
        user = users_collection.find_one({
            "$or": [
                {"username": username},
                {"email": username}
            ]
        })
        
        if not user:
            return "❌ Invalid username or password"
        
        # Verify password
        if user["password_hash"] != hash_password(password):
            return "❌ Invalid username or password"
        
        # Generate session token and expiration time
        session_token = generate_session_token()
        expires_at = datetime.now() + timedelta(hours=SESSION_TIMEOUT_HOURS)
        
        # Update user with session token and expiration
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "session_token": session_token,
                "session_expires_at": expires_at,
                "last_login": datetime.now()
            }}
        )
        
        return f"✓ Login successful!\nUser ID: {user['_id']}\nSession Token: {session_token}\nExpires: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n⚠️ Save this session token - you'll need it for all expense operations!\n💡 Session valid for {SESSION_TIMEOUT_HOURS} hours"
    except PyMongoError as e:
        return f"❌ Error during login: {str(e)}"


@mcp.tool
def check_session_status(session_token: str) -> str:
    """
    Check the status and expiration time of a session token.
    
    Args:
        session_token: User's session token
    
    Returns:
        Session status information
    """
    try:
        db = get_db_connection()
        users_collection = db["users"]
        
        user = users_collection.find_one({"session_token": session_token})
        
        if not user:
            return "❌ Invalid session token"
        
        if not user.get("session_expires_at"):
            return "⚠️ Session found but no expiration set (legacy session)"
        
        expires_at = user["session_expires_at"]
        now = datetime.now()
        
        if now > expires_at:
            return f"❌ Session expired at {expires_at.strftime('%Y-%m-%d %H:%M:%S')}"
        
        time_remaining = expires_at - now
        hours_remaining = time_remaining.total_seconds() / 3600
        
        result = f"✓ Session is valid\n"
        result += f"User: {user['username']}\n"
        result += f"Expires at: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        result += f"Time remaining: {hours_remaining:.1f} hours"
        
        return result
    except PyMongoError as e:
        return f"❌ Error checking session: {str(e)}"


@mcp.tool
def logout_user(session_token: str) -> str:
    """
    Logout a user by invalidating their session token.
    
    Args:
        session_token: User's current session token
    
    Returns:
        Success or error message
    """
    try:
        db = get_db_connection()
        users_collection = db["users"]
        
        result = users_collection.update_one(
            {"session_token": session_token},
            {"$set": {"session_token": None, "session_expires_at": None}}
        )
        
        if result.modified_count > 0:
            return "✓ Logged out successfully"
        else:
            return "❌ Invalid session token"
    except PyMongoError as e:
        return f"❌ Error during logout: {str(e)}"


def get_user_from_token(session_token: str):
    """
    Get user document from session token and validate expiration.
    
    Args:
        session_token: User's session token
    
    Returns:
        User document or None (if token invalid or expired)
    """
    try:
        db = get_db_connection()
        users_collection = db["users"]
        
        # Find user with this token
        user = users_collection.find_one({"session_token": session_token})
        
        if not user:
            return None
        
        # Check if session has expired
        if user.get("session_expires_at"):
            if datetime.now() > user["session_expires_at"]:
                # Session expired - clear the token
                users_collection.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"session_token": None, "session_expires_at": None}}
                )
                return None
        
        return user
    except PyMongoError:
        return None


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
def add_expense(session_token: str, description: str, amount: float, category: str) -> str:
    """
    Add an expense to the expense tracker database for the logged-in user.
    
    Args:
        session_token: User's session token (obtained from login)
        description: Description of the expense
        amount: Amount spent
        category: Category of the expense
    
    Returns:
        Success message or error
    """
    try:
        # Verify user session
        user = get_user_from_token(session_token)
        if not user:
            return "❌ Invalid session token. Please login first."
        
        db = get_db_connection()
        expenses_collection = db["expenses"]
        
        expense_doc = {
            "user_id": user["_id"],
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
def list_all_expense(session_token: str) -> str:
    """
    List all expenses for the logged-in user.
    
    Args:
        session_token: User's session token
    
    Returns:
        List of user's expenses
    """
    try:
        # Verify user session
        user = get_user_from_token(session_token)
        if not user:
            return "❌ Invalid session token. Please login first."
        
        db = get_db_connection()
        expenses_collection = db["expenses"]
        
        expenses = list(expenses_collection.find({"user_id": user["_id"]}).sort("_id", 1))
        
        if expenses:
            result = f"📋 Your Expenses (User: {user['username']}):\n" + "="*60 + "\n"
            for expense in expenses:
                result += f"ID: {expense['_id']}\n"
                result += f"  Description: {expense['description']}\n"
                result += f"  Amount: ${expense['amount']:.2f}\n"
                result += f"  Category: {expense.get('category', 'N/A')}\n"
                result += f"  Date: {expense['date']}\n"
                result += "-"*60 + "\n"
            return result
        else:
            return "No expenses found for your account"
    except PyMongoError as e:
        return f"❌ Error listing expenses: {str(e)}"


@mcp.tool
def search_expense(session_token: str, search_term: str) -> str:
    """
    Search for expenses by description or category for the logged-in user.
    
    Args:
        session_token: User's session token
        search_term: Text to search for in description or category
    
    Returns:
        Formatted list of matching expenses
    """
    try:
        # Verify user session
        user = get_user_from_token(session_token)
        if not user:
            return "❌ Invalid session token. Please login first."
        
        db = get_db_connection()
        expenses_collection = db["expenses"]
        
        # Search in description and category using regex, filtered by user_id
        query = {
            "user_id": user["_id"],
            "$or": [
                {"description": {"$regex": search_term, "$options": "i"}},
                {"category": {"$regex": search_term, "$options": "i"}}
            ]
        }
        
        expenses = list(expenses_collection.find(query).sort("_id", 1))
        
        if expenses:
            result = f"🔍 Search results for '{search_term}' (User: {user['username']}):\n" + "="*60 + "\n"
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
def get_expense_details_by_date_and_category(session_token: str, start_date: str, end_date: str, category: Optional[str] = None) -> str:
    """
    Get detailed list of expenses between two dates for the logged-in user, optionally filtered by category.

    Args:
        session_token: User's session token
        start_date: The start date of the range (format: YYYY-MM-DD)
        end_date: The end date of the range (format: YYYY-MM-DD)
        category: The category to filter by (optional)

    Returns:
        Detailed list of expenses with all information
    """
    try:
        # Verify user session
        user = get_user_from_token(session_token)
        if not user:
            return "❌ Invalid session token. Please login first."
        
        db = get_db_connection()
        expenses_collection = db["expenses"]
        
        # Build query based on whether category is provided
        query: dict = {
            "user_id": user["_id"],
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
def get_expense_summary_by_date_and_category(session_token: str, start_date: str, end_date: str, category: Optional[str] = None) -> str:
    """
    Get grouped summary of expenses between two dates for the logged-in user, optionally filtered and grouped by category.
    
    Args:
        session_token: User's session token
        start_date: The start date of the range (format: YYYY-MM-DD)
        end_date: The end date of the range (format: YYYY-MM-DD)
        category: The category to filter by (optional)
    
    Returns:
        Formatted summary with expenses grouped by category, showing totals
    """
    try:
        # Verify user session
        user = get_user_from_token(session_token)
        if not user:
            return "❌ Invalid session token. Please login first."
        
        db = get_db_connection()
        expenses_collection = db["expenses"]
        
        # Build query based on whether category is provided
        query: dict = {
            "user_id": user["_id"],
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
def get_expense_details(session_token: str, expense_id: str) -> str:
    """
    Get detailed information about a specific expense by ID for the logged-in user.
    
    Args:
        session_token: User's session token
        expense_id: The MongoDB ObjectId of the expense to retrieve (as string)
    
    Returns:
        Detailed expense information
    """
    try:
        # Verify user session
        user = get_user_from_token(session_token)
        if not user:
            return "❌ Invalid session token. Please login first."
        
        db = get_db_connection()
        expenses_collection = db["expenses"]
        
        expense = expenses_collection.find_one({"_id": ObjectId(expense_id), "user_id": user["_id"]})
        
        if expense:
            result = f"📄 Expense Details (ID: {expense['_id']}):\n" + "="*60 + "\n"
            result += f"Description: {expense['description']}\n"
            result += f"Amount: ${expense['amount']:.2f}\n"
            result += f"Category: {expense.get('category', 'N/A')}\n"
            result += f"Date: {expense['date']}\n"
            result += f"Created: {expense['created_at']}\n"
            return result
        else:
            return f"❌ Expense with ID {expense_id} not found or doesn't belong to you"
    except Exception as e:
        return f"❌ Error getting expense: {str(e)}"


@mcp.tool
def delete_expense(session_token: str, description: str) -> str:
    """
    Delete expenses from the expense tracker database by description for the logged-in user.
    
    Args:
        session_token: User's session token
        description: Description of the expense(s) to delete
    
    Returns:
        Success or error message
    """
    try:
        # Verify user session
        user = get_user_from_token(session_token)
        if not user:
            return "❌ Invalid session token. Please login first."
        
        db = get_db_connection()
        expenses_collection = db["expenses"]
        
        result = expenses_collection.delete_many({"user_id": user["_id"], "description": description})
        
        if result.deleted_count > 0:
            return f"✓ Deleted {result.deleted_count} expense(s) successfully"
        else:
            return f"❌ No expenses found with description '{description}'"
    except PyMongoError as e:
        return f"❌ Error deleting expense: {str(e)}"


@mcp.tool
def modify_expense(session_token: str, description: str, amount: float) -> str:
    """
    Modify an expense amount in the expense tracker database for the logged-in user.
    
    Args:
        session_token: User's session token
        description: Description of the expense(s) to modify
        amount: New amount for the expense(s)
    
    Returns:
        Success or error message
    """
    try:
        # Verify user session
        user = get_user_from_token(session_token)
        if not user:
            return "❌ Invalid session token. Please login first."
        
        db = get_db_connection()
        expenses_collection = db["expenses"]
        
        result = expenses_collection.update_many(
            {"user_id": user["_id"], "description": description},
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
