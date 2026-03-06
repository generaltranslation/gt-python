"""Test script for the FastAPI lazy example.

Start the app first: uv run uvicorn app:app --port 8001
Then run: uv run python scripts/test_endpoints.py
"""

import httpx

BASE_URL = "http://localhost:8001"


def test_endpoint(
    path: str, locale: str, expected_substr: str, name: str
) -> None:
    headers = {"Accept-Language": locale}
    resp = httpx.get(f"{BASE_URL}{path}", headers=headers)
    body = resp.json()
    status = "PASS" if expected_substr in body["message"] else "FAIL"
    print(f"  [{status}] {name}: {body['message']}")


def main() -> None:
    print("=== FastAPI Lazy Example ===\n")

    print("GET /")
    test_endpoint("/", "en", "Hello, world!", "English")
    test_endpoint("/", "es", "Hola, mundo!", "Spanish")
    test_endpoint("/", "fr", "Bonjour, le monde!", "French")

    print("\nGET /greet?name=Alice")
    test_endpoint("/greet?name=Alice", "en", "Hello, Alice!", "English")
    test_endpoint("/greet?name=Alice", "es", "Hola, Alice!", "Spanish")
    test_endpoint("/greet?name=Alice", "fr", "Bonjour, Alice!", "French")

    print()


if __name__ == "__main__":
    main()
