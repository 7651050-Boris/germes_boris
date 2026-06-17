# Announcing JOIN-able Reference Tables to the LLM

When you add a reference table (e.g., `wagon_specs`) that enriches the main data
table, the bot's LLM must know it can JOIN. This is done through the DB_SCHEMA
string — not through code changes.

## Pattern

Add a section to DB_SCHEMA that describes the reference table and shows a
working JOIN example:

```
ДОПОЛНИТЕЛЬНАЯ ТАБЛИЦА ref_table (краткое описание):
Можно JOIN по key_column. Колонки:
- col1 — описание
- col2 — описание

Пример JOIN:
SELECT w.col, r.col
FROM main_table w
LEFT JOIN ref_table r ON w.key = r.key
WHERE w.id = '12345'

Для вопросов про X — используй r.col.
```

## Critical: Update Default SELECT Rule

When you add a new column to the main table or reference table, update the
bot's default SELECT rule so the column appears in results:

```
# Before:
6. Для списка: SELECT col1, col2 FROM main_table WHERE ...

# After:
6. Для списка: SELECT col1, col2, new_col FROM main_table WHERE ...
```

Without this, the LLM may not include the column even when relevant.

## When to Add to Default SELECT

- Columns that answer common questions (ownership, model, capacity)
- Columns that provide immediate context (category, type, status)
- NOT: raw IDs, internal codes, rarely-queried technical fields

## Verification

After updating DB_SCHEMA, restart the bot and test:
1. A query that naturally benefits from the JOIN → LLM should use it
2. A query that doesn't need the JOIN → LLM should NOT use it (no unnecessary JOINs)
3. The default SELECT rule should include the new column in list results
