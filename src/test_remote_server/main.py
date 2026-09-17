from fastmcp import FastMCP
import os
import sqlite3
import json

CATEGORIES_PATH = os.path.join(
    os.path.dirname(__file__),
    "categories.json"
)
DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")

mcp = FastMCP("Expense Tracker")

def load_categories():
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS EXPENSES(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dATE TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT NOT NULL DEFAULT '',
            note TEXT DEFAULT ''
            )
            """)

init_db()
@mcp.tool()
def add_expense(
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    note: str = ""
):
    """Add a new expense entry to database."""

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            INSERT INTO expenses
            (date, amount, category, subcategory, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (date, amount, category, subcategory, note)
        )

        return {"status": "ok", "id": cur.lastrowid}

@mcp.tool()
def list_expenses_by_date_range(start_date: str, end_date: str):
    """List expenses between two dates, including both dates."""

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC, id ASC
            """,
            (start_date, end_date)
        )

        cols = [d[0] for d in cur.description]

        return [
            dict(zip(cols, row))
            for row in cur.fetchall()
        ]

@mcp.tool()
def edit_expense(
    expense_id: int,
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    note: str = ""
):
    """Update an existing expense."""

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            UPDATE expenses
            SET date = ?,
                amount = ?,
                category = ?,
                subcategory = ?,
                note = ?
            WHERE id = ?
            """,
            (
                date,
                amount,
                category,
                subcategory,
                note,
                expense_id
            )
        )

        if cur.rowcount == 0:
            return {
                "status": "error",
                "message": f"Expense {expense_id} not found"
            }

        return {
            "status": "ok",
            "message": f"Expense {expense_id} updated"
        }

@mcp.tool()
def delete_expense(expense_id: int):
    """Delete an expense by its ID."""

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "DELETE FROM expenses WHERE id = ?",
            (expense_id,)
        )

        if cur.rowcount == 0:
            return {
                "status": "error",
                "message": f"Expense {expense_id} not found"
            }

        return {
            "status": "ok",
            "message": f"Expense {expense_id} deleted"
        }

@mcp.tool()
def get_total_expenses() -> float:
    """Calculate the total amount of all expenses."""

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses"
        )

        total = cur.fetchone()[0]

        return float(total)

@mcp.tool()
def get_expenses_by_category(category: str):
    """List all expenses for a specific category."""

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE category = ?
            ORDER BY date ASC, id ASC
            """,
            (category,)
        )

        cols = [d[0] for d in cur.description]

        return [
            dict(zip(cols, row))
            for row in cur.fetchall()
        ]

@mcp.tool()
def list_categories():
    """List all available expense categories and subcategories."""
    return load_categories()



# start the server
if __name__=="__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)