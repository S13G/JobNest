import json
import threading

import websocket

# Replace this with the WebSocket URL of your Django Channels server
websocket_url = "ws://127.0.0.1:8000/ws/chat/<user-id>?token=<authenticated-user-jwt-token>"


def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") == "chat_message":
        print(f"Received message: {data['message']}")


def on_error(ws, error):
    print(f"Error: {error}")


def on_close(ws, close_status_code, close_msg):
    print("Closed")


def on_open(ws):
    # Start a separate thread to handle user input
    threading.Thread(target=send_messages, args=(ws,), daemon=True).start()


def send_messages(ws):
    while True:
        user_input = input("Type a message (or 'exit' to quit): ")
        if user_input.lower() == 'exit':
            ws.close()
            break

        message_data = {
            "type": "chat_message",
            "message": user_input
        }
        ws.send(json.dumps(message_data))


if __name__ == "__main__":
    # Connect to the Django Channels WebSocket server
    ws = websocket.WebSocketApp(websocket_url,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    ws.on_open = on_open
    ws.run_forever()
