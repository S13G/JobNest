import json
import signal
import sys

import websocket

# Replace this with the WebSocket URL of your Django Channels server
# USER ID OF AUTHENTICATED USER
# TOKEN OF AUTHENTICATED USER
websocket_url = "ws://127.0.0.1:8000/ws/notification/<user_id>?token=<token>"


def on_message(ws, message):
    # This function is called whenever a message is received from the server
    data = json.loads(message)
    print(f"Received notification: {data['message']}")


def on_error(ws, error):
    # This function is called whenever there is an error with the WebSocket connection
    print(f"Error: {error}")


def on_close(ws, close_status_code, close_msg):
    # This function is called when the WebSocket connection is closed
    print("Connection closed")


def on_open(ws):
    # This function is called when the WebSocket connection is opened
    print("WebSocket connection opened. Waiting for notifications...")


def signal_handler(signal, frame):
    print("Exiting...")
    ws.close()
    sys.exit(0)


if __name__ == "__main__":
    # Set up signal handler for graceful exit
    signal.signal(signal.SIGINT, signal_handler)

    # Create a WebSocketApp instance and run it
    ws = websocket.WebSocketApp(websocket_url,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()
