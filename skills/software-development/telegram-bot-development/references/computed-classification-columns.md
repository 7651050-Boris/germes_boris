# Computed Classification Columns in SQLite

Pattern for deriving categorical labels from combinations of existing columns using `CASE WHEN`.

## When to Use

- Multiple columns encode overlapping information (e.g., `ownership` + `lease_flag` + `lessee`)
- User wants a single filterable column summarizing complex business logic
- Classification rules are deterministic and expressible in SQL

## Pattern

```sql
ALTER TABLE main_table ADD COLUMN computed_category TEXT;

UPDATE main_table SET computed_category = 
CASE 
    WHEN condition_1 THEN 'Label A'
    WHEN condition_2 THEN 'Label B'
    WHEN condition_3 THEN 'Label C'
    ELSE 'Label D'
END;

CREATE INDEX idx_computed_cat ON main_table(computed_category);
```

## Real Example: Ownership Classification

Classifying railway wagons into four ownership categories from three columns:

```sql
ALTER TABLE wagons ADD COLUMN ownership_category TEXT;

UPDATE wagons SET ownership_category = 
CASE 
    -- Leasing companies: owners with "лизинг" in name, ГТЛК, ТрансФин, etc.
    WHEN owner LIKE '%лизинг%' 
      OR owner LIKE '%ГТЛК%' 
      OR owner LIKE '%ТрансФин%' 
      OR owner LIKE '%ВЭБ%лиз%' 
      OR owner LIKE '%РЕСО%лиз%' 
      OR owner LIKE '%СБЕР%лиз%'
    THEN 'Лизинг'
    
    -- State inventory park
    WHEN ownership = 'ИП' 
      OR owner LIKE '%Инвентарный парк%'
    THEN 'Инвентарный парк'
    
    -- Owner leasing to someone else
    WHEN lessee != '' 
      AND lessee IS NOT NULL 
      AND lessee != '00000000' 
      AND lease_flag = 'Аренда'
    THEN 'Собственник-арендодатель'
    
    -- Everyone else: operates their own fleet
    ELSE 'Собственник'
END;

CREATE INDEX idx_ownership_cat ON wagons(ownership_category);
```

## Announce to Bot's LLM

Add the column to the bot's DB_SCHEMA so it can filter by it:

```
ownership_category — категория владения: Собственник, Собственник-арендодатель, Инвентарный парк, Лизинг
```

Also add it to the default SELECT list for results to show the category.

## Verification

```sql
SELECT ownership_category, COUNT(*) FROM main_table GROUP BY 1 ORDER BY 2 DESC;
```

Expected: each row falls into exactly one category, total matches original row count.

## Pitfalls

1. **CASE WHEN order matters** — first matching condition wins. Put most specific conditions first (leasing company names before generic patterns).
2. **NULL handling** — `NULL LIKE '%pattern%'` is NULL (not TRUE). Always add `IS NOT NULL` for nullable columns.
3. **Sentinel values** — watch for "00000000" or empty strings as valid-not-valid records. Add explicit exclusion in conditions.
4. **Large tables** — ALTER TABLE + UPDATE on 1.7M rows takes ~10 seconds in SQLite. Acceptable for one-time migration.
