# MongoDB Atlas Setup Guide

This guide will help you set up MongoDB Atlas (cloud MongoDB) for your expense tracker application.

## Step 1: Create a MongoDB Atlas Account

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Sign up for a free account (no credit card required)
3. Verify your email address

## Step 2: Create a New Cluster

1. After logging in, click **"Build a Database"** or **"Create"**
2. Choose the **FREE** tier (M0 Sandbox)
3. Select your preferred cloud provider and region (choose one closest to you)
4. Give your cluster a name (e.g., "expense-tracker-cluster")
5. Click **"Create Cluster"** (this may take 3-5 minutes)

## Step 3: Create a Database User

1. In the left sidebar, click **"Database Access"** under Security
2. Click **"Add New Database User"**
3. Choose **"Password"** authentication method
4. Enter a username (e.g., "expense_user")
5. Click **"Autogenerate Secure Password"** or create your own strong password
6. **IMPORTANT:** Copy and save this password securely - you'll need it for the connection string
7. Under "Database User Privileges", select **"Read and write to any database"**
8. Click **"Add User"**

## Step 4: Configure Network Access

1. In the left sidebar, click **"Network Access"** under Security
2. Click **"Add IP Address"**
3. For development, you can click **"Allow Access from Anywhere"** (0.0.0.0/0)
   - **Note:** For production, restrict this to specific IP addresses
4. Click **"Confirm"**

## Step 5: Get Your Connection String

1. Go back to **"Database"** in the left sidebar
2. Click **"Connect"** button on your cluster
3. Select **"Connect your application"**
4. Choose **"Python"** as the driver and select version **"3.12 or later"**
5. Copy the connection string - it will look like:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

## Step 6: Update Your .env File

1. Open the `.env` file in your project
2. Replace the placeholder connection string with your actual connection string
3. Replace `<username>` with your database username
4. Replace `<password>` with your database password
5. Add the database name after `.mongodb.net/` like this:
   ```
   MONGODB_URL=mongodb+srv://expense_user:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/expense_tracker?retryWrites=true&w=majority
   ```

### Example .env file:

```env
MONGODB_URL=mongodb+srv://expense_user:MySecurePass123@cluster0.abc123.mongodb.net/expense_tracker?retryWrites=true&w=majority
```

## Step 7: Test Your Connection

Run your application to test the connection:

```bash
python main.py
```

If successful, you should see:

```
✓ MongoDB database initialized successfully
```

## Step 8: View Your Data (Optional)

1. In MongoDB Atlas, go to **"Database"** → **"Browse Collections"**
2. You'll see your `expense_tracker` database and `expenses` collection
3. You can view, edit, and manage your data directly from the Atlas interface

## Troubleshooting

### Connection Timeout

- Check that your IP address is whitelisted in Network Access
- Verify your internet connection

### Authentication Failed

- Double-check your username and password in the connection string
- Ensure there are no special characters that need URL encoding in your password
- If your password contains special characters, URL encode them:
  - `@` → `%40`
  - `:` → `%3A`
  - `/` → `%2F`
  - `?` → `%3F`
  - `#` → `%23`

### Database Not Found

- The database will be created automatically when you first insert data
- Make sure you've added the database name to your connection string

## Security Best Practices

1. **Never commit your .env file to version control** (it's already in .gitignore)
2. Use strong, unique passwords for database users
3. Restrict network access to specific IP addresses in production
4. Rotate your database passwords regularly
5. Use different credentials for development and production environments

## Local MongoDB Alternative

If you prefer to use MongoDB locally instead of Atlas:

1. Install MongoDB Community Edition from [mongodb.com/try/download/community](https://www.mongodb.com/try/download/community)
2. Start MongoDB service
3. Update your `.env` file:
   ```env
   MONGODB_URL=mongodb://localhost:27017/expense_tracker
   ```

## Additional Resources

- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [MongoDB Python Driver (PyMongo) Documentation](https://pymongo.readthedocs.io/)
- [MongoDB University - Free Courses](https://university.mongodb.com/)
