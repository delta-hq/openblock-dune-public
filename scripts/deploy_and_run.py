#!/usr/bin/env python3
"""
Comprehensive Dune Query Deployment and Execution Script

This script provides the complete workflow you want:
1. Create new queries from local SQL files
2. Update existing queries
3. Trigger query execution
4. Optionally wait for results

Usage:
    python3 scripts/deploy_and_run.py                    # Deploy all and run
    python3 scripts/deploy_and_run.py --create-only      # Just create new queries
    python3 scripts/deploy_and_run.py --run-only         # Just run existing queries
    python3 scripts/deploy_and_run.py --query-id 5526654 # Run specific query
"""

import os
import yaml
import argparse
import time
from dune_client.client import DuneClient
from dune_client.query import QueryBase
from dotenv import load_dotenv
import sys
import codecs

# Set the default encoding to UTF-8
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)

dune = DuneClient.from_env()


def load_queries_config():
    """Load queries.yml configuration"""
    queries_yml_path = os.path.join(os.path.dirname(__file__), "..", "queries.yml")
    with open(queries_yml_path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    query_ids = data.get("query_ids", [])
    if query_ids is None:
        query_ids = []
    return data, query_ids


def save_queries_config(data):
    """Save queries.yml configuration"""
    queries_yml_path = os.path.join(os.path.dirname(__file__), "..", "queries.yml")
    with open(queries_yml_path, "w", encoding="utf-8") as file:
        yaml.dump(data, file, default_flow_style=False, sort_keys=False)


def create_new_queries():
    """Create new queries from SQL files without query IDs"""
    print("🔍 Looking for new SQL files to create as Dune queries...")

    queries_path = os.path.join(os.path.dirname(__file__), "..", "queries")
    data, existing_ids = load_queries_config()

    # Find SQL files that don't have query IDs yet
    sql_files = [f for f in os.listdir(queries_path) if f.endswith(".sql")]
    new_files = [f for f in sql_files if "___" not in f]

    if not new_files:
        print("✅ No new SQL files found.")
        return []

    created_queries = []

    for file in new_files:
        file_path = os.path.join(queries_path, file)

        with open(file_path, "r", encoding="utf-8") as f:
            sql_content = f.read()

        if not sql_content.strip():
            print(f"⏭️  Skipping empty file: {file}")
            continue

        query_name = file.replace(".sql", "").replace("_", " ").title()

        try:
            print(f"📝 Creating Dune query: {query_name}")

            response = dune.create_query(
                name=query_name, query_sql=sql_content, is_private=False
            )

            query_id = response.query_id
            print(f"✅ Created query '{query_name}' with ID: {query_id}")

            # Rename file to include query ID
            new_filename = f"{file.replace('.sql', '')}___{query_id}.sql"
            new_file_path = os.path.join(queries_path, new_filename)
            os.rename(file_path, new_file_path)
            print(f"📝 Renamed file to: {new_filename}")

            created_queries.append(query_id)

        except Exception as e:
            print(f"❌ Error creating query from {file}: {str(e)}")

    # Update queries.yml
    if created_queries:
        all_ids = list(existing_ids) + created_queries
        all_ids = [id for id in all_ids if id is not None]
        data["query_ids"] = all_ids
        save_queries_config(data)
        print(f"📋 Updated queries.yml with new IDs: {created_queries}")

    return created_queries


def update_existing_queries():
    """Update existing queries from local SQL files"""
    print("🔄 Updating existing queries...")

    _, existing_ids = load_queries_config()
    queries_path = os.path.join(os.path.dirname(__file__), "..", "queries")

    updated_count = 0

    for query_id in existing_ids:
        if query_id is None:
            continue

        # Find the corresponding file
        files = os.listdir(queries_path)
        matching_files = [
            f for f in files if str(query_id) == f.split("___")[-1].split(".")[0]
        ]

        if not matching_files:
            print(f"⚠️  No local file found for query ID {query_id}")
            continue

        file_path = os.path.join(queries_path, matching_files[0])

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                sql_content = file.read()

            query = dune.get_query(query_id)
            print(f"🔄 Updating query {query_id}: {query.base.name}")

            dune.update_query(
                query_id=query_id,
                query_sql=sql_content,
            )
            print(f"✅ Updated query {query_id}")
            updated_count += 1

        except Exception as e:
            print(f"❌ Error updating query {query_id}: {str(e)}")

    print(f"✅ Updated {updated_count} existing queries")
    return updated_count


def run_queries(query_ids=None, wait_for_results=True):
    """Execute queries and optionally wait for results"""
    if query_ids is None:
        _, query_ids = load_queries_config()

    if not query_ids:
        print("❌ No queries to run")
        return

    print(f"🚀 Running {len(query_ids)} queries...")

    execution_ids = []

    for query_id in query_ids:
        if query_id is None:
            continue

        try:
            query = dune.get_query(query_id)
            print(f"▶️  Running query {query_id}: {query.base.name}")

            execution = dune.run_query(query_id)
            execution_ids.append((query_id, execution.execution_id, query.base.name))
            print(f"🎯 Started execution {execution.execution_id}")

        except Exception as e:
            print(f"❌ Error running query {query_id}: {str(e)}")

    if wait_for_results and execution_ids:
        print("\n⏳ Waiting for query results...")

        for query_id, execution_id, name in execution_ids:
            print(f"⌛ Waiting for {name} (execution {execution_id})...")

            try:
                # Wait for completion with timeout
                result = dune.get_execution_results(execution_id)
                print(f"✅ Query {query_id} completed successfully")
                print(f"📊 Rows returned: {len(result.rows)}")

            except Exception as e:
                print(f"❌ Error getting results for query {query_id}: {str(e)}")

    return execution_ids


def main():
    parser = argparse.ArgumentParser(description="Deploy and run Dune queries")
    parser.add_argument(
        "--create-only",
        action="store_true",
        help="Only create new queries, don't update or run",
    )
    parser.add_argument(
        "--update-only",
        action="store_true",
        help="Only update existing queries, don't create or run",
    )
    parser.add_argument(
        "--run-only",
        action="store_true",
        help="Only run queries, don't create or update",
    )
    parser.add_argument("--query-id", type=int, help="Run specific query ID only")
    parser.add_argument(
        "--no-wait", action="store_true", help="Don't wait for query results"
    )

    args = parser.parse_args()

    print("🚀 Dune Query Deployment and Execution")
    print("=" * 50)

    created_queries = []
    updated_count = 0

    # Create new queries
    if not args.update_only and not args.run_only:
        created_queries = create_new_queries()
        print()

    # Update existing queries
    if not args.create_only and not args.run_only:
        updated_count = update_existing_queries()
        print()

    # Run queries
    if not args.create_only and not args.update_only:
        query_ids_to_run = None
        if args.query_id:
            query_ids_to_run = [args.query_id]

        executions = run_queries(
            query_ids=query_ids_to_run, wait_for_results=not args.no_wait
        )
        print()

    # Summary
    print("📋 Summary:")
    print(f"   📝 Created: {len(created_queries)} new queries")
    print(f"   🔄 Updated: {updated_count} existing queries")
    if not args.create_only and not args.update_only:
        executed_count = len(
            [q for q in (query_ids_to_run or load_queries_config()[1]) if q]
        )
        print(f"   🚀 Executed: {executed_count} queries")

    print("\n✅ Deployment complete!")


if __name__ == "__main__":
    main()
