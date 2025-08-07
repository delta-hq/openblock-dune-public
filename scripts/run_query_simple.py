#!/usr/bin/env python3
"""
Simple Query Execution Script - Trigger Only
Only triggers query execution without pulling results to save credits
"""

import os
import requests
import time
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)


def run_query_simple(query_id):
    """Run a query using direct API calls"""
    api_key = os.getenv("DUNE_API_KEY")
    if not api_key:
        print("❌ DUNE_API_KEY not found in .env file")
        return

    headers = {"x-dune-api-key": api_key}

    # Step 1: Execute the query
    execute_url = f"https://api.dune.com/api/v1/query/{query_id}/execute"
    print(f"🚀 Executing query {query_id}...")

    try:
        response = requests.post(execute_url, headers=headers)
        if response.status_code == 200:
            execution_id = response.json().get("execution_id")
            print(f"✅ Query execution started: {execution_id}")

            # Step 2: Wait for completion
            print("⏳ Waiting for query to complete...")
            status_url = f"https://api.dune.com/api/v1/execution/{execution_id}/status"

            while True:
                status_response = requests.get(status_url, headers=headers)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    state = status_data.get("state")

                    if state == "QUERY_STATE_COMPLETED":
                        print("✅ Query completed successfully!")
                        print("🔗 View results at:")
                        print(f"https://dune.com/queries/{query_id}")
                        break

                    elif state == "QUERY_STATE_FAILED":
                        print("❌ Query failed")
                        break

                    elif state in [
                        "QUERY_STATE_PENDING",
                        "QUERY_STATE_RUNNING",
                        "QUERY_STATE_EXECUTING",
                    ]:
                        print(f"⏳ Status: {state}")
                        time.sleep(5)  # Wait 5 seconds before checking again
                    else:
                        print(f"⚠️  Unknown state: {state}")
                        break
                else:
                    print(f"❌ Error checking status: {status_response.status_code}")
                    break

        else:
            print(f"❌ Error executing query: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python3 scripts/run_query_simple.py <query_id>")
        sys.exit(1)

    query_id = sys.argv[1]
    run_query_simple(query_id)
