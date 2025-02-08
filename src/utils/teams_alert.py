import requests
import json
import os

webhook_url = os.getenv("TEAMS_WEBHOOK_URL")


async def send_alert(text: str):
    """Teams 알림 전송"""

    # message = create_teams_message(text)

    # response = requests.post(
    #     webhook_url,
    #     headers={"Content-Type": "application/json"},
    #     data=json.dumps(message),
    # )

    # return response


def create_teams_message(text: str) -> dict:
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.2",
                    "body": [
                        {
                            "type": "Container",
                            "style": "default",
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": text,
                                    "weight": "bolder",
                                    "size": "medium",
                                    "isSubtle": False,
                                },
                            ],
                            "bleed": True,
                        }
                    ],
                    "msteams": {"width": "Full"},
                },
            }
        ],
    }