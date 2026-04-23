import json
import requests

def test_whatsapp_webhook():
    url = "https://kinyan-crm-new-1.onrender.com/webhooks/whatsapp"
    payload = [
        {
            "typeWebhook": "incomingMessageReceived",
            "idMessage": "3EB0F2B15421DA48161A1C",
            "instanceData": {
                "idInstance": 7105597557,
                "wid": "972559443507@c.us",
                "typeInstance": "whatsapp"
            },
            "timestamp": 1776939111,
            "senderData": {
                "chatId": "972527180504@c.us",
                "sender": "972527180504@c.us",
                "senderName": "אייזיק קליין",
                "senderContactName": "",
                "chatName": "אייזיק קליין"
            },
            "messageData": {
                "typeMessage": "textMessage",
                "textMessageData": {
                    "textMessage": "מה קורה"
                }
            }
        }
    ]
    
    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_whatsapp_webhook()
