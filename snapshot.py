import os
import requests
from datetime import datetime, timezone, timedelta

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
SOURCE_DB_ID = os.environ["SOURCE_DB_ID"]
TARGET_DB_ID = os.environ["TARGET_DB_ID"]

NOTION_VERSION = "2022-06-28"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}

VN_TZ = timezone(timedelta(hours=7))
today = datetime.now(VN_TZ).date().isoformat()


def query_database(database_id):
    url = f"https://api.notion.com/v1/databases/{database_id}/query"

    results = []
    payload = {}

    while True:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()

        results.extend(data["results"])

        if not data.get("has_more"):
            break

        payload["start_cursor"] = data["next_cursor"]

    return results


def get_title(prop):
    items = prop.get("title", [])

    if not items:
        return "Untitled"

    return "".join([x["plain_text"] for x in items])


def get_select(prop):
    value = prop.get("select")

    if not value:
        return None

    return value["name"]


def get_number(prop):
    return prop.get("number")


def create_snapshot(name, status, dev, art, source_page_id):

    url = "https://api.notion.com/v1/pages"

    properties = {
        "Name": {
            "title": [
                {
                    "text": {
                        "content": name
                    }
                }
            ]
        },
        "Date": {
            "date": {
                "start": today
            }
        },
        "Source Page ID": {
            "rich_text": [
                {
                    "text": {
                        "content": source_page_id
                    }
                }
            ]
        }
    }

    if status:
        properties["Status"] = {
            "select": {
                "name": status
            }
        }

    if dev is not None:
        properties["Dev %"] = {
            "number": dev
        }

    if art is not None:
        properties["Art %"] = {
            "number": art
        }

    payload = {
        "parent": {
            "database_id": TARGET_DB_ID
        },
        "properties": properties
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload
    )

    response.raise_for_status()


def main():

    rows = query_database(SOURCE_DB_ID)

    for row in rows:

        props = row["properties"]

        name = get_title(props["Name"])
        status = get_select(props["Status"])
        dev = get_number(props["Dev %"])
        art = get_number(props["Art %"])

        create_snapshot(
            name=name,
            status=status,
            dev=dev,
            art=art,
            source_page_id=row["id"]
        )

    print(f"Created {len(rows)} snapshot rows")


if __name__ == "__main__":
    main()
