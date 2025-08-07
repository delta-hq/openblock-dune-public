# Using This Repo as a Private dbt Package

This guide explains how to use this repository as a private dbt package in your data warehouse project.

## 1. Create Private Repository

First, create a private copy of this repository:

```bash
# Clone this repo
git clone https://github.com/your-username/openblock-dune-public.git openblock-dune-private

# Create new private repo on GitHub
# Then update the remote
cd openblock-dune-private
git remote set-url origin https://github.com/your-username/openblock-dune-private.git
git push -u origin main
```

## 2. Configure Access

### Option A: Deploy Key (Recommended)
1. Generate a deploy key:
   ```bash
   ssh-keygen -t ed25519 -C "your@email.com" -f ~/.ssh/openblock_dune_public_deploy
   ```

2. Add the public key to your private repo:
   - Go to Settings → Deploy Keys
   - Add the contents of `~/.ssh/openblock_dune_public_deploy.pub`
   - Enable "Allow write access" if needed

3. Add the private key to your dbt project's secrets:
   - Add to GitHub Secrets if using GitHub Actions
   - Add to your CI/CD environment variables
   - Name it `DBT_DEPLOY_KEY`

### Option B: Personal Access Token
1. Create a fine-grained PAT in GitHub
2. Add to your environment as `GITHUB_PAT`

## 3. Add to Your dbt Project

### In your dbt project's `packages.yml`:

```yaml
packages:
  # Your private Dune package
  - git: "git@github.com:your-username/openblock-dune-private.git"
    revision: main  # or specific tag/commit
  
  # Required dependencies
  - package: duneanalytics/dune
    version: 1.0.0
```

### Configure Dune API Access

In your dbt project's `profiles.yml`:

```yaml
your_project:
  target: dev
  outputs:
    dev:
      type: snowflake  # or your warehouse
      # ... your warehouse config ...
      
      # Dune API configuration
      dune:
        api_key: "{{ env_var('DUNE_API_KEY') }}"
```

## 4. Use the Models

### Import Staging Data
```sql
-- models/staging/stg_my_model.sql
SELECT * FROM {{ ref('stg_vesu_balances') }}
```

### Use Transformed Data
```sql
-- models/marts/my_model.sql
SELECT * FROM {{ ref('vesu_balances') }}
```

## 5. Customize the Package

### Override Variables
In your `dbt_project.yml`:
```yaml
vars:
  dune_lookback_days: 14  # Change default 7 days
```

### Override Model Configs
```yaml
models:
  openblock_dune_public:
    staging:
      +schema: raw_dune  # Change default schema
```

## 6. Development Workflow

### Update Dune Queries
1. Edit queries in `/queries` folder
2. Run `python3 scripts/deploy_and_run.py`
3. Commit and push changes

### Add New Models
1. Create new `.sql` files in `models/`
2. Update `schema.yml` with documentation
3. Add query IDs to `dbt_project.yml`

## 7. CI/CD Setup

### GitHub Actions Example
```yaml
name: dbt CI

on:
  push:
    branches: [ main ]

jobs:
  dbt-run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install SSH Key
        uses: webfactory/ssh-agent@v0.7.0
        with:
          ssh-private-key: ${{ secrets.DBT_DEPLOY_KEY }}
      
      - name: dbt deps & run
        env:
          DUNE_API_KEY: ${{ secrets.DUNE_API_KEY }}
        run: |
          dbt deps
          dbt run --select openblock_dune.*
```

## 8. Best Practices

1. **Version Control**:
   - Tag releases with semantic versioning
   - Use specific revisions in `packages.yml`

2. **Testing**:
   - Add dbt tests to `schema.yml`
   - Test incremental logic carefully

3. **Documentation**:
   - Document model changes
   - Keep query IDs updated

4. **Security**:
   - Never commit API keys
   - Use deploy keys or fine-grained PATs
   - Keep repo private

## 9. Troubleshooting

### Common Issues

1. **SSH Key Access**:
   ```bash
   # Test SSH access
   ssh -T git@github.com -i ~/.ssh/openblock_dune_public_deploy
   ```

2. **Package Not Found**:
   ```bash
   # Clear dbt package cache
   rm -rf dbt_packages
   dbt clean
   dbt deps
   ```

3. **Dune API Issues**:
   ```bash
   # Test API key
   python3 scripts/run_query_simple.py 5526654
   ```

### Support

For issues:
1. Check query status on Dune
2. Verify API key permissions
3. Check dbt logs
4. Open an issue in the repo 