# User Authentication System

This expense tracker now includes a complete user authentication system with user-specific expense tracking.

## Overview

The system uses two MongoDB collections:

1. **users** - Stores user account information
2. **expenses** - Stores expenses with user_id as a foreign key

Each user can only view and manage their own expenses. All expense operations require a valid session token obtained through login.

## Database Schema

### Users Collection

```javascript
{
  _id: ObjectId,
  username: String (unique),
  email: String (unique),
  password_hash: String (SHA-256 hashed),
  session_token: String (nullable),
  created_at: DateTime,
  last_login: DateTime
}
```

### Expenses Collection

```javascript
{
  _id: ObjectId,
  user_id: ObjectId (foreign key to users),
  description: String,
  amount: Float,
  category: String,
  date: String (YYYY-MM-DD),
  created_at: DateTime
}
```

## Authentication Flow

### 1. User Registration

Register a new user account:

```python
register_user(
    username="john_doe",
    email="john@example.com",
    password="secure_password123"
)
```

**Response:**

```
✓ User registered successfully! User ID: 507f1f77bcf86cd799439011
```

### 2. User Login

Login to get a session token:

```python
login_user(
    username="john_doe",  # Can also use email
    password="secure_password123"
)
```

**Response:**

```
✓ Login successful!
User ID: 507f1f77bcf86cd799439011
Session Token: abc123xyz789...

⚠️ Save this session token - you'll need it for all expense operations!
```

**Important:** Save the session token - you'll need it for all subsequent operations.

### 3. Using the Session Token

All expense operations now require the session token as the first parameter:

```python
# Add an expense
add_expense(
    session_token="abc123xyz789...",
    description="Lunch at restaurant",
    amount=25.50,
    category="Food & Dining"
)

# List all your expenses
list_all_expense(session_token="abc123xyz789...")

# Search your expenses
search_expense(
    session_token="abc123xyz789...",
    search_term="lunch"
)
```

### 4. Check Session Status

Check if your session is still valid and when it expires:

```python
check_session_status(session_token="abc123xyz789...")
```

**Response:**

```
✓ Session is valid
User: john_doe
Expires at: 2026-01-29 12:00:00
Time remaining: 18.5 hours
```

### 5. Logout

Invalidate your session token:

```python
logout_user(session_token="abc123xyz789...")
```

## Available Functions

### Authentication Functions

#### `register_user(username, email, password)`

- Creates a new user account
- Username and email must be unique
- Password is automatically hashed using SHA-256

#### `login_user(username, password)`

- Authenticates user and generates session token
- Can use either username or email for login
- Returns session token needed for all operations

#### `logout_user(session_token)`

- Invalidates the session token
- User must login again to perform operations

### Expense Functions (All require session_token)

#### `add_expense(session_token, description, amount, category)`

- Adds an expense for the logged-in user
- Automatically associates expense with user_id

#### `list_all_expense(session_token)`

- Lists all expenses for the logged-in user only
- Other users' expenses are not visible

#### `search_expense(session_token, search_term)`

- Searches expenses for the logged-in user
- Searches in description and category fields

#### `get_expense_details_by_date_and_category(session_token, start_date, end_date, category=None)`

- Gets detailed expense list for date range
- Only shows logged-in user's expenses
- Optional category filter

#### `get_expense_summary_by_date_and_category(session_token, start_date, end_date, category=None)`

- Gets grouped summary by category
- Only includes logged-in user's expenses
- Shows totals and breakdowns

#### `get_expense_details(session_token, expense_id)`

- Gets details of a specific expense
- Only works if expense belongs to logged-in user

#### `delete_expense(session_token, description)`

- Deletes expenses matching description
- Only deletes logged-in user's expenses

#### `modify_expense(session_token, description, amount)`

- Updates expense amount
- Only modifies logged-in user's expenses

## Security Features

1. **Password Hashing**: Passwords are hashed using SHA-256 before storage
2. **Session Tokens**: Secure random tokens generated using `secrets.token_urlsafe(32)`
3. **Session Expiration**: Automatic token expiration after configurable timeout (default: 24 hours)
4. **Automatic Cleanup**: Expired sessions are invalidated automatically on access
5. **User Isolation**: Each user can only access their own expenses
6. **Unique Constraints**: Username and email must be unique
7. **Database Indexes**: Optimized queries with proper indexing on session_expires_at

## Example Usage Workflow

```python
# 1. Register a new user
register_user("alice", "alice@example.com", "mypassword123")

# 2. Login to get session token
response = login_user("alice", "mypassword123")
# Save the session token from response

# 3. Add expenses
add_expense(
    session_token="your_token_here",
    description="Grocery shopping",
    amount=85.50,
    category="Food & Dining"
)

add_expense(
    session_token="your_token_here",
    description="Gas",
    amount=45.00,
    category="Transportation"
)

# 4. View your expenses
list_all_expense(session_token="your_token_here")

# 5. Get summary for a date range
get_expense_summary_by_date_and_category(
    session_token="your_token_here",
    start_date="2026-01-01",
    end_date="2026-01-31"
)

# 6. Check session status
check_session_status(session_token="your_token_here")

# 7. Logout when done
logout_user(session_token="your_token_here")
```

## Session Configuration

Configure session timeout in your `.env` file:

```env
# Session timeout in hours (default: 24)
SESSION_TIMEOUT_HOURS=24
```

**Examples:**

- `SESSION_TIMEOUT_HOURS=1` - Sessions expire after 1 hour
- `SESSION_TIMEOUT_HOURS=12` - Sessions expire after 12 hours
- `SESSION_TIMEOUT_HOURS=168` - Sessions expire after 1 week (7 days)

## Error Handling

All functions return clear error messages:

- `❌ Invalid session token. Please login first.` - Session expired or invalid
- `❌ Session expired at 2026-01-29 12:00:00` - Session has expired, login again
- `❌ Username 'john_doe' already exists` - Username taken
- `❌ Email 'john@example.com' already registered` - Email already in use
- `❌ Invalid username or password` - Login failed
- `❌ Expense with ID xxx not found or doesn't belong to you` - Access denied

## Database Initialization

The database is automatically initialized with both collections when you run:

```python
python main.py
```

This creates:

- `users` collection with indexes on username, email, and session_token
- `expenses` collection with indexes on user_id, date, category, and description

## Migration from Old System

If you have existing expenses without user_id:

1. Create user accounts for existing data
2. Update old expenses to assign them to appropriate users
3. Add user_id field to all existing expense documents

## Best Practices

1. **Store Session Tokens Securely**: Never share or expose session tokens
2. **Logout When Done**: Always logout to invalidate session tokens
3. **Use Strong Passwords**: Encourage users to use strong, unique passwords
4. **Regular Token Rotation**: Consider implementing token expiration for production
5. **HTTPS in Production**: Always use HTTPS when deploying to production

## Future Enhancements

Potential improvements for production use:

- Token expiration and refresh mechanism
- Password reset functionality
- Email verification
- Two-factor authentication (2FA)
- Rate limiting for login attempts
- Password strength requirements
- Account recovery options
- Audit logging for security events
