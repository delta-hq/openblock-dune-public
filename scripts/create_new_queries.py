import os
import yaml
from dune_client.client import DuneClient
from dotenv import load_dotenv
import sys
import codecs

# Set the default encoding to UTF-8
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)

dune = DuneClient.from_env()


def create_queries_from_files():
    """
    Automatically create Dune queries from SQL files in the /queries folder
    that don't have query IDs yet (files without ___<id> suffix)
    """
    queries_path = os.path.join(os.path.dirname(__file__), "..", "queries")
    queries_yml_path = os.path.join(os.path.dirname(__file__), "..", "queries.yml")

    # Read current queries.yml
    with open(queries_yml_path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    # Handle case where query_ids exists but is None (only comments)
    query_ids = data.get("query_ids", [])
    if query_ids is None:
        query_ids = []
    existing_ids = set(query_ids)

    # Find SQL files that don't have query IDs yet
    sql_files = [f for f in os.listdir(queries_path) if f.endswith(".sql")]
    new_files = []

    for file in sql_files:
        # Check if file already has a query ID (format: name___<id>.sql)
        if "___" not in file:
            new_files.append(file)

    if not new_files:
        print("No new SQL files found to create queries from.")
        return

    created_queries = []

    for file in new_files:
        file_path = os.path.join(queries_path, file)

        # Read the SQL content
        with open(file_path, "r", encoding="utf-8") as f:
            sql_content = f.read()

        if not sql_content.strip():
            print(f"Skipping empty file: {file}")
            continue

        # Generate query name from filename
        query_name = file.replace(".sql", "").replace("_", " ").title()

        try:
            print(f"Creating Dune query: {query_name}")

            # Create the query in Dune
            response = dune.create_query(
                name=query_name, query_sql=sql_content, is_private=False
            )

            query_id = response.query_id
            print(f"✅ Created query '{query_name}' with ID: {query_id}")

            # Rename the local file to include the query ID
            new_filename = f"{file.replace('.sql', '')}___{query_id}.sql"
            new_file_path = os.path.join(queries_path, new_filename)
            os.rename(file_path, new_file_path)
            print(f"📝 Renamed file to: {new_filename}")

            created_queries.append(query_id)

        except Exception as e:
            print(f"❌ Error creating query from {file}: {str(e)}")

    # Update queries.yml with new query IDs
    if created_queries:
        all_ids = list(existing_ids) + created_queries
        # Remove None values and ensure all are integers
        all_ids = [id for id in all_ids if id is not None]

        data["query_ids"] = all_ids

        with open(queries_yml_path, "w", encoding="utf-8") as file:
            yaml.dump(data, file, default_flow_style=False, sort_keys=False)

        print(f"\n🎉 Successfully created {len(created_queries)} new queries!")
        print(f"📋 Updated queries.yml with IDs: {created_queries}")
        print("\nNext steps:")
        print("1. Your queries are now live on Dune")
        print("2. Use 'python3 scripts/preview_query.py <ID>' to test them")
        print("3. Use 'python3 scripts/push_to_dune.py' to sync future changes")


if __name__ == "__main__":
    create_queries_from_files()
