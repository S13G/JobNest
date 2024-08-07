import json
import threading

import websocket

# Replace this with the WebSocket URL of your Django Channels server
# User ID - USER TO SEND MESSAGE TO
# Authenticated User Token
websocket_url = "ws://127.0.0.1:8000/ws/chat/<user_id>?token=<authenticated_user_token>"


def on_message(ws, message):
    # This function is called whenever a message is received from the server
    data = json.loads(message)
    print(f"Received message: {data}")


def on_error(ws, error):
    # This function is called whenever there is an error with the WebSocket connection
    print(f"Error: {error}")


def on_close(ws, close_status_code, close_msg):
    # This function is called when the WebSocket connection is closed
    print("Closed")


def on_open(ws):
    # This function is called when the WebSocket connection is opened
    # It starts a new thread to handle user input
    threading.Thread(target=send_messages, args=(ws,), daemon=True).start()


def send_messages(ws):
    # This function handles sending messages from user input
    while True:
        user_input = input("Type a message (or 'exit' to quit): ")
        if user_input.lower() == 'exit':
            ws.close()
            break

        message_data = {
            "text": user_input
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
