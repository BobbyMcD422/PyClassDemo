import csv
import sys
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener


BASE_URL = "http://localhost:5000"


def test_login(username, password, base_url=BASE_URL):
    """Try one fake classroom login and return True if it reaches the dashboard."""
    cookies = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cookies))

    form_data = urlencode({"username": username, "password": password}).encode()
    request = Request(
        f"{base_url}/login",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    response = opener.open(request)
    page = response.read().decode("utf-8")

    return response.url == f"{base_url}/" and username in page


def load_users(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def main():
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("users.csv")
    users = load_users(csv_path)

    failures = []
    for user in users:
        username = user["username"]
        password = user["password"]

        if test_login(username, password):
            print(f"PASS {username}")
        else:
            print(f"FAIL {username}")
            failures.append(username)

    print()
    print(f"Checked {len(users)} users. Passed {len(users) - len(failures)}. Failed {len(failures)}.")

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
