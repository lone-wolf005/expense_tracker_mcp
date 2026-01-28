# Expense Tracker with User Authentication

A comprehensive expense tracking system with user authentication, built using MongoDB and FastMCP. Each user has their own isolated expense data with secure session-based authentication.

## Features

✅ **User Authentication**

- Secure user registration and login
- Session token-based authentication
- Password hashing (SHA-256)
- User-specific expense isolation

✅ **Expense Management**

- Add, view, search, update, and delete expenses
- Categorized expense tracking
- Date-based filtering and summaries
- Detailed expense reports

✅ **Multi-User Support**

- Each user has their own expense data
- Complete data isolation between users
- Secure session management

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install pymongo python-dotenv fastmcp
```

### 2. Database Setup

Configure your MongoDB connection in `.env`:

```env
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/expenseTracker?retryWrites=true&w=majority
```

See [`MONGODB_SETUP.md`](MONGODB_SETUP.md) for detailed MongoDB Atlas setup instructions.

### 3. Initialize Database

```bash
python main.py
```

This will create the required collections and indexes.

## Usage

### Authentication Workflow

#### 1. Register a New User

```python
register_user(
    username="john_doe",
    email="john@example.com",
    password="secure_password"
)
```

#### 2. Login

```python
login_user(
    username="john_doe",
    password="secure_password"
)
```

**Save the session token from the response!** You'll need it for all operations.

**Note:** Sessions expire after 24 hours by default. You can configure this in `.env` with `SESSION_TIMEOUT_HOURS`.

#### 3. Add Expenses

```python
add_expense(
    session_token="your_session_token_here",
    description="Lunch at restaurant",
    amount=25.50,
    category="Food & Dining"
)
```

#### 4. View Your Expenses

```python
# List all expenses
list_all_expense(session_token="your_session_token_here")

# Search expenses
search_expense(
    session_token="your_session_token_here",
    search_term="lunch"
)

# Get summary by date range
get_expense_summary_by_date_and_category(
    session_token="your_session_token_here",
    start_date="2026-01-01",
    end_date="2026-01-31"
)
```

#### 5. Check Session Status

```python
check_session_status(session_token="your_session_token_here")
```

#### 6. Logout

```python
logout_user(session_token="your_session_token_here")
```

## Available Categories

The system includes predefined categories:

- 🍔 Food & Dining
- 🚗 Transportation
- 🛍️ Shopping
- 💡 Bills & Utilities
- 🎬 Entertainment
- 🏥 Health
- 📚 Education
- 🧍 Personal
- 📈 Investments
- 📦 Others

View all categories and subcategories:

```python
list_available_categories()
```

## API Functions

### Authentication

| Function                                   | Description                                     |
| ------------------------------------------ | ----------------------------------------------- |
| `register_user(username, email, password)` | Create a new user account                       |
| `login_user(username, password)`           | Login and get session token (expires after 24h) |
| `check_session_status(session_token)`      | Check if session is valid and when it expires   |
| `logout_user(session_token)`               | Logout and invalidate token                     |

### Expense Management

All expense functions require `session_token` as the first parameter:

| Function                                                                                  | Description                    |
| ----------------------------------------------------------------------------------------- | ------------------------------ |
| `add_expense(session_token, description, amount, category)`                               | Add a new expense              |
| `list_all_expense(session_token)`                                                         | List all your expenses         |
| `search_expense(session_token, search_term)`                                              | Search expenses                |
| `get_expense_details(session_token, expense_id)`                                          | Get specific expense details   |
| `get_expense_details_by_date_and_category(session_token, start_date, end_date, category)` | Get expenses by date range     |
| `get_expense_summary_by_date_and_category(session_token, start_date, end_date, category)` | Get grouped summary            |
| `delete_expense(session_token, description)`                                              | Delete expenses by description |
| `modify_expense(session_token, description, amount)`                                      | Update expense amount          |

### Utility

| Function                      | Description                 |
| ----------------------------- | --------------------------- |
| `list_available_categories()` | View all expense categories |

## Database Structure

### Users Collection

```javascript
{
  _id: ObjectId,
  username: String (unique),
  email: String (unique),
  password_hash: String,
  session_token: String,
  session_expires_at: DateTime,
  created_at: DateTime,
  last_login: DateTime
}
```

### Expenses Collection

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,  // Foreign key to users
  description: String,
  amount: Float,
  category: String,
  date: String (YYYY-MM-DD),
  created_at: DateTime
}
```

## Security Features

- 🔒 Password hashing using SHA-256
- 🎫 Secure session token generation
- ⏰ Automatic session expiration (configurable, default: 24 hours)
- 👤 User-specific data isolation
- 🔐 Session-based authentication
- 📊 Indexed database queries for performance

## Documentation

- [`AUTHENTICATION.md`](AUTHENTICATION.md) - Detailed authentication system documentation
- [`MONGODB_SETUP.md`](MONGODB_SETUP.md) - MongoDB Atlas setup guide
- [`categories.json`](categories.json) - Available expense categories

## Project Structure

```
expense-tracker/
├── main.py                 # Main application with MCP server
├── test.py                 # SQLite version (legacy)
├── categories.json         # Expense categories definition
├── .env                    # MongoDB connection string
├── README.md              # This file
├── AUTHENTICATION.md      # Authentication documentation
└── MONGODB_SETUP.md       # MongoDB setup guide
```

## Example Session

```python
# 1. Register
register_user("alice", "alice@example.com", "password123")

# 2. Login
response = login_user("alice", "password123")
# Response: ✓ Login successful! Session Token: abc123...

# 3. Add expenses
token = "abc123..."  # From login response

add_expense(token, "Grocery shopping", 85.50, "Food & Dining")
add_expense(token, "Gas", 45.00, "Transportation")
add_expense(token, "Movie tickets", 30.00, "Entertainment")

# 4. View expenses
list_all_expense(token)

# 5. Get monthly summary
get_expense_summary_by_date_and_category(
    token,
    "2026-01-01",
    "2026-01-31"
)

# 6. Logout
logout_user(token)
```

## Error Handling

The system provides clear error messages:

- `❌ Invalid session token. Please login first.` - Token expired or invalid
- `❌ Session expired at 2026-01-29 12:00:00` - Session has expired
- `❌ Username already exists`
- `❌ Email already registered`
- `❌ Invalid username or password`
- `❌ No expenses found`

## Requirements

- Python 3.8+
- MongoDB (Atlas or local)
- pymongo
- python-dotenv
- fastmcp

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:

1. Check [`AUTHENTICATION.md`](AUTHENTICATION.md) for authentication details
2. Check [`MONGODB_SETUP.md`](MONGODB_SETUP.md) for database setup
3. Review the error messages for troubleshooting hints

---

**Made with Bob** 🤖
