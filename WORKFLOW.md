# Dune Query Workflow Guide

## For New Queries (Like Your vesu_user_balances.sql)

### Step 1: Create Query in Dune Web Interface

1. **Go to Dune**: https://dune.com/
2. **Click "New Query"**
3. **Paste your SQL** from `queries/vesu_user_balances.sql`
4. **Add a title**: "Vesu User Balances"
5. **Save the query**
6. **Note the Query ID** from the URL: `https://dune.com/queries/<QUERY_ID>/...`

### Step 2: Add Query ID to queries.yml

```yaml
query_ids:
  - YOUR_QUERY_ID_HERE  # Vesu User Balances
```

### Step 3: Pull Query to Sync Locally

```bash
python3 scripts/pull_from_dune.py
```

This will:
- Download your query from Dune
- Create/update `queries/vesu_user_balances___YOUR_ID.sql`
- Keep the local and Dune versions in sync

### Step 4: Make Edits Locally & Push

```bash
# Make your edits to the local .sql file
python3 scripts/push_to_dune.py
```

## For Existing Queries

If you already have query IDs in `queries.yml`:

### Pull Latest from Dune
```bash
python3 scripts/pull_from_dune.py
```

### Test a Query
```bash
python3 scripts/preview_query.py <QUERY_ID>
```

### Push Local Changes to Dune
```bash
python3 scripts/push_to_dune.py
```

## Understanding Query Results

- **Dune queries** return data that can be consumed by APIs
- **This repo manages the SQL**, not the data itself
- **For dbt integration**, you'll query Dune's API from your dbt models

## Next Steps for dbt Integration

Once your queries are working in Dune:

1. **Use Dune's dbt package** in your consuming project:
   ```yaml
   # In your main dbt project's packages.yml
   packages:
     - package: duneanalytics/dune
       version: 1.0.0
   ```

2. **Query Dune from dbt models**:
   ```sql
   -- In your dbt models
   {{ dune.query('YOUR_QUERY_ID') }}
   ```

3. **Or use this repo as a package** for query management:
   ```yaml
   packages:
     - git: "https://github.com/your-username/openblock-dune-public.git"
   ``` 