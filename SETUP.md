# Data Ingestion Setup Guide

This repository is set up for basic blockchain data ingestion using Dune Analytics queries and is configured to be used as a dbt package in other projects.

## Prerequisites

1. **Dune Plus Plan**: You need a Dune Plus plan to access the API
2. **Python 3.7+**: Required for running the Dune scripts
3. **Dune Account**: With team access and API key generation permissions

## Initial Setup

### 1. Environment Configuration

Create a `.env` file in the root directory:

```bash
# Copy the template and fill in your values
cp .env.example .env
```

Edit `.env` with your actual values:
```bash
DUNE_API_KEY=your_actual_api_key_here
DUNE_TEAM_NAME=your_team_name  # Optional
```

Get your API key from: https://dune.com/settings/api

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Your Queries

1. **Create queries in Dune**: First, create your data ingestion queries in the Dune web interface
2. **Get query IDs**: From the URL `https://dune.com/queries/<query_id>/...`
3. **Update queries.yml**: Add your actual query IDs to `queries.yml`

Example:
```yaml
query_ids:
  - 1234567  # Your raw blocks query
  - 2345678  # Your ERC20 transfers query  
  - 3456789  # Your DeFi transactions query
```

### 4. Pull Queries from Dune

```bash
python scripts/pull_from_dune.py
```

This will create `.sql` files in the `/queries` folder with your actual query content.

## Example Queries Provided

The repository includes three example queries in `/example_queries/`:

1. **`raw_ethereum_blocks.sql`**: Extracts raw Ethereum block data (7-day lookback)
2. **`erc20_transfers.sql`**: Gets ERC20 token transfer events (1-day lookback)  
3. **`defi_transactions.sql`**: Captures DeFi protocol transactions from major platforms

You can use these as templates for your own queries.

## Using as a dbt Package

This repository is configured to work as a dbt package. In your main dbt project:

### 1. Add to packages.yml

```yaml
packages:
  - git: "https://github.com/your-username/openblock-dune-public.git"
    revision: main
```

### 2. Install the package

```bash
dbt deps
```

### 3. Configure variables (optional)

In your `dbt_project.yml`:
```yaml
vars:
  openblock_dune_ingestion:
    blocks_lookback_days: 7
    transfers_lookback_days: 1
    defi_lookback_days: 1
```

## Workflow

### Development Workflow

1. **Develop queries** in Dune web interface
2. **Test queries** with `python scripts/preview_query.py <query_id>`
3. **Pull queries** with `python scripts/pull_from_dune.py` 
4. **Make edits** in your local files
5. **Push changes** with `python scripts/push_to_dune.py` or commit to trigger GitHub Actions

### Data Upload Workflow

1. **Add CSV files** to `/uploads` folder
2. **Upload to Dune** with `python scripts/upload_to_dune.py`
3. Tables will be available as `dune.{team_name}.dataset_{filename}`

## GitHub Actions

The repository includes automated workflows that:
- Push query changes to Dune when you commit to main
- Upload CSV files to Dune as tables
- Run on every commit to the main branch

Make sure to add your `DUNE_API_KEY` to GitHub Secrets.

## Available Scripts

| Script | Purpose | Command |
|--------|---------|---------|
| `pull_from_dune.py` | Download queries from Dune to local files | `python scripts/pull_from_dune.py` |
| `push_to_dune.py` | Upload local query changes to Dune | `python scripts/push_to_dune.py` |
| `preview_query.py` | Test a query and see first 20 rows | `python scripts/preview_query.py <query_id>` |
| `upload_to_dune.py` | Upload CSV files as Dune tables | `python scripts/upload_to_dune.py` |

## Next Steps

1. **Create your Dune queries** using the provided examples as templates
2. **Update queries.yml** with your actual query IDs
3. **Pull and test** your queries locally
4. **Set up your consuming dbt project** to use this as a package
5. **Configure GitHub Actions** with your `DUNE_API_KEY`

## Troubleshooting

- **API errors**: Ensure you have a Dune Plus plan and valid API key
- **Query not found**: Make sure query IDs are correct and you own the queries
- **Permission errors**: Verify your API key has access to the team/queries
- **File encoding issues**: The scripts handle UTF-8 encoding automatically

## Repository Structure

```
openblock-dune-public/
├── .env.example              # Environment template
├── queries.yml               # Query ID configuration
├── dbt_project.yml          # dbt package configuration
├── packages.yml             # dbt dependencies
├── models/
│   └── schema.yml           # dbt model documentation
├── example_queries/         # Example query templates
├── queries/                 # Your actual Dune queries (auto-generated)
├── uploads/                 # CSV files for Dune table uploads
└── scripts/                 # Management scripts
``` 