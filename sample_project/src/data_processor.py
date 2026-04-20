# sample_project/src/data_processor.py
# This file has intentional bugs for the agent to find and fix

import json
import os

def load_config(path):
    # BUG: file handle never closed (resource leak)
    f = open(path, "r")
    return json.load(f)

def calculate_average(numbers):
    # BUG: ZeroDivisionError when list is empty
    return sum(numbers) / len(numbers)

def get_user_data(user_id):
    # BUG: SQL injection vulnerability (string formatting in query)
    query = "SELECT * FROM users WHERE id = %s" % user_id
    return query

def read_env_secret():
    # BUG: hardcoded secret instead of env var
    api_key = "sk-prod-abc123supersecret"
    return api_key

def process_items(items):
    results = []
    for i in range(len(items)):
        # BUG: should use enumerate, also IndexError risk if items mutated
        results.append(items[i] * 2)
    return results


if __name__ == "__main__":
    print(calculate_average([10, 20, 30]))
    print(process_items([1, 2, 3]))
