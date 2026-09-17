from fastmcp import FastMCP
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
import os
import aiosqlite
import json

CATEGORIES_PATH = os.path.join(
    os.path.dirname(__file__),
    "categories.json"
)

DB_PATH = os.environ.get(
    "DB_PATH",
    "/tmp/expenses.db"
)


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT NOT NULL DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)
        await db.commit()


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Initialize database when the MCP server starts."""
    await init_db()

    try:
        yield
    finally:
        pass


mcp = FastMCP(
    "Expense Tracker",
    lifespan=app_lifespan
)


def load_categories():
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@mcp.tool()
async def add_expense(
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    note: str = ""
):
    """Add a new expense entry to database."""

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO expenses
            (date, amount, category, subcategory, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (date, amount, category, subcategory, note)
        )

        await db.commit()

        return {
            "status": "ok",
            "id": cursor.lastrowid
        }


@mcp.tool()
async def list_expenses_by_date_range(
    start_date: str,
    end_date: str
):
    """List expenses between two dates, including both dates."""

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC, id ASC
            """,
            (start_date, end_date)
        )

        rows = await cursor.fetchall()

        columns = [column[0] for column in cursor.description]

        return [
            dict(zip(columns, row))
            for row in rows
        ]


@mcp.tool()
async def edit_expense(
    expense_id: int,
    date: str,
    amount: float,
    category: str,
    subcategory: str = "",
    note: str = ""
):
    """Update an existing expense."""

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
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

        await db.commit()

        if cursor.rowcount == 0:
            return {
                "status": "error",
                "message": f"Expense {expense_id} not found"
            }

        return {
            "status": "ok",
            "message": f"Expense {expense_id} updated"
        }


@mcp.tool()
async def delete_expense(expense_id: int):
    """Delete an expense by its ID."""

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM expenses WHERE id = ?",
            (expense_id,)
        )

        await db.commit()

        if cursor.rowcount == 0:
            return {
                "status": "error",
                "message": f"Expense {expense_id} not found"
            }

        return {
            "status": "ok",
            "message": f"Expense {expense_id} deleted"
        }


@mcp.tool()
async def get_total_expenses() -> float:
    """Calculate the total amount of all expenses."""

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses"
        )

        row = await cursor.fetchone()

        return float(row[0])


@mcp.tool()
async def get_expenses_by_category(category: str):
    """List all expenses for a specific category."""

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE category = ?
            ORDER BY date ASC, id ASC
            """,
            (category,)
        )

        rows = await cursor.fetchall()

        columns = [column[0] for column in cursor.description]

        return [
            dict(zip(columns, row))
            for row in rows
        ]


@mcp.tool()
def list_categories():
    """List all available expense categories and subcategories."""
    return load_categories()


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000
    )