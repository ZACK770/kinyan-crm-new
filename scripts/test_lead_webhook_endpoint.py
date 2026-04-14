#!/usr/bin/env python3
import argparse
import json

import requests


def main():
    parser = argparse.ArgumentParser(description="Smoke test for the unified lead webhook endpoint")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base server URL")
    parser.add_argument("--skip-post", action="store_true", help="Only run the GET diagnostic check")
    args = parser.parse_args()

    endpoint = f"{args.base_url.rstrip('/')}/webhooks/lead"

    print(f"Checking GET {endpoint}")
    get_response = requests.get(endpoint, timeout=15)
    print(f"GET status: {get_response.status_code}")
    print(get_response.text)

    if args.skip_post:
        return

    payload = {
        "phone": "0501234567",
        "name": "Lead Endpoint Test",
        "source_type": "script-test",
        "source_name": "test_lead_webhook_endpoint.py",
    }

    print(f"\nChecking POST {endpoint}")
    post_response = requests.post(endpoint, json=payload, timeout=15)
    print(f"POST status: {post_response.status_code}")
    try:
        print(json.dumps(post_response.json(), ensure_ascii=False, indent=2))
    except Exception:
        print(post_response.text)


if __name__ == "__main__":
    main()