1.scalar():
    This method is used to execute a query and return the first element of the first result, or None if there are no results.
    It does not raise an exception if no rows are returned; it simply returns None.
    If more than one row is returned, it still only returns the first element of the first row and ignores the rest.


scalar_one():
    This method is similar to scalar(), but it expects exactly one row to be returned.
    If no rows are returned, it raises a NoResultFound exception.
    If more than one row is returned, it raises a MultipleResultsFound exception.
    This is useful when you expect a single result and want to enforce that expectation.

scalar_one_or_none():
    This method is a hybrid between scalar() and scalar_one().
    It returns the first element of the first result if a row is found, otherwise it returns None.
    Unlike scalar_one(), it does not raise an exception if no rows are returned.
    However, if more than one row is returned, it raises a MultipleResultsFound exception.


scalars():
    This method is used to execute a query and return an iterator of scalar values.
    It returns all the scalar values from the first column of each row in the result set.
    This is useful when you want to retrieve a list of scalar values from a query.



HTTPBearer is a FastAPI class used to extract the Bearer token from the Authorization header (like Authorization: Bearer <token>).





why use Redis for logout

    Problem:
    JWTs are stateless — once issued, they can't be invalidated unless:
    They expire naturally (exp claim).
    The server keeps a blocklist of revoked tokens.
    If a user logs out or a token is compromised, the backend needs a way to track revoked tokens — but without storing JWTs, you can't "log out" effectively.


    ✅ Redis solves this:
    Store revoked tokens (JTI) with expiry matching the token’s expiry (ex=3600).

    Every request can check: “Is this token’s JTI in Redis?”

    If yes → reject the token.

    If no → allow access.

        Login → Issue JWT → Use in requests

        Logout → Add JWT's JTI to Redis blocklist (with expiry)

        Next request → Check if JTI in Redis
            → If found: reject
            → If not found: allow





### 🔄 SQLAlchemy: `joinedload` vs `selectinload`

SQLAlchemy provides two eager loading strategies to efficiently load related data and avoid the N+1 query problem:

---

### 🔗 `joinedload`

✅ **What it does:**
- Loads related data via a **single query** using a **SQL JOIN**.
- Parent and child rows come together.

📌 **Example:**
```python
from sqlalchemy.orm import joinedload

stmt = select(User).options(joinedload(User.addresses))
result = await session.execute(stmt)
users = result.scalars().all()
```

⚠️ **When to use:**
- Relationships like **one-to-one** or **many-to-one**.
- When you need related data **immediately**.
- When the join **won’t cause large row duplication** (data explosion).

---

### 📥 `selectinload`

✅ **What it does:**
- Executes **two separate queries**:
  - One for parent data.
  - Another for related data using an `IN` clause on foreign keys.
- More efficient for collections.

📌 **Example:**
```python
from sqlalchemy.orm import selectinload

stmt = select(User).options(selectinload(User.addresses))
result = await session.execute(stmt)
users = result.scalars().all()
```

⚠️ **When to use:**
- Relationships like **one-to-many** or **many-to-many**.
- When JOINs would create **too many rows** due to fan-out.
- When you want to **avoid duplication** from JOINs.

---

### 🆚 Summary Comparison

| Feature                | `joinedload`                          | `selectinload`                        |
|------------------------|----------------------------------------|----------------------------------------|
| Number of queries      | 1                                      | 2+                                     |
| Query type             | SQL JOIN                               | Separate `IN` query                    |
| Best for               | One-to-one, many-to-one                | One-to-many, many-to-many              |
| Data duplication risk  | Higher (due to JOINs)                  | Lower                                  |
| Performance            | Good for small, flat data              | Better for larger, nested data         |
| SQL visibility         | All in one query                       | Easier to debug separate queries       |

---

✅ **Quick Rule of Thumb:**

- Use `joinedload` when the relationship is small and tight (e.g., user -> role).
- Use `selectinload` when you're loading collections or want to avoid JOIN overhead.


############################################################################################



## ✅ Row Duplication & Large JOINs in SQLAlchemy

When using `joinedload()` with one-to-many relationships (e.g., `User → Books`), SQLAlchemy creates a JOIN query that causes **row duplication**.

---

### 🔍 Scenario:
- 1 User (`Alice`)
- 3 Books (`Book A`, `Book B`, `Book C`)

---

### ⚠️ Using `joinedload(User.books)`:

SQL Query:
```sql
SELECT users.id, users.name, books.id, books.title
FROM users
LEFT OUTER JOIN books ON users.id = books.user_id
WHERE users.id = 1;
```

Result:
| users.id | users.name | books.id | books.title |
|----------|------------|----------|-------------|
| 1        | Alice      | 101      | Book A      |
| 1        | Alice      | 102      | Book B      |
| 1        | Alice      | 103      | Book C      |

➡️ **User data is repeated for each book**

📌 This is called **row duplication** and:
- Slows down performance
- Requires `.unique()` in SQLAlchemy to deduplicate rows
- Can be problematic if there are many child records

---

### ✅ Using `selectinload(User.books)`:

SQLAlchemy runs **two separate queries**:

Query 1:
```sql
SELECT * FROM users WHERE id = 1;
```

Query 2:
```sql
SELECT * FROM books WHERE user_id IN (1);
```

➡️ No duplication
➡️ Efficient in memory
➡️ Preferred for one-to-many relationships

---

### 📊 Example: 1000 users, 50 books each

- With `joinedload`: 1000 × 50 = **50,000 joined rows**
- With `selectinload`: 1 query for 1000 users + 1 query for 50,000 books

✅ `selectinload` scales better and avoids row explosion

---

## 🧠 Summary

| Term                | Explanation |
|---------------------|-------------|
| **Row duplication** | Repeating parent rows (e.g., User) for each child (e.g., Book) |
| **Large JOINs**     | One big query that returns excessive rows |
| **selectinload**    | Uses separate optimized queries (best for one-to-many) |
| **joinedload**      | Single query with JOIN (use for one-to-one or small collections) |

---
