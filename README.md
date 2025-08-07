# Dune Query Version Control

A template for managing Dune Analytics queries with version control and automated deployment. All data stays in Dune - no external warehouse needed!

## Quick Start

```bash
# 1. Set up environment
cp .env.example .env  # Add your DUNE_API_KEY

# 2. Add your query ID to queries.yml
query_ids:
  - 5526654  # Your Vesu balances query

# 3. Pull existing query to sync locally
python3 scripts/pull_from_dune.py

# 4. Make changes and deploy
vim queries/vesu_daily_user_balances___5526654.sql
python3 scripts/deploy_and_run.py
```

## How It Works

1. **All Data Stays in Dune**
   - Queries run in Dune's environment
   - Results are cached by Dune
   - No external warehouse needed

2. **Version Control Benefits**
   - Track query changes
   - Collaborate with team
   - Roll back if needed

3. **Automated Deployment**
   - Push changes to Dune
   - Trigger refreshes
   - No manual copy/paste

## Available Commands

| Command | Purpose |
|---------|---------|
| `python3 scripts/deploy_and_run.py` | Update query in Dune + run |
| `python3 scripts/run_query_simple.py <id>` | Just run the query |

## Query Organization

```
queries/
└── vesu_daily_user_balances___5526654.sql  # Your query
```

## Credits Usage

- Queries run in Dune's environment
- Uses Dune's native caching
- No additional materialization costs

## GitHub Actions

The repository includes automated workflows that:
- Push query changes to Dune when you commit
- Run queries on schedule if needed
- Notify on failures

## Next Steps

1. Add your queries to `queries.yml`
2. Use git for version control
3. Let GitHub Actions handle deployment

Need help? Check the docs or open an issue!
