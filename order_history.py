import requests
import time
import hashlib
import hmac
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

# Replace these with your Bybit API credentials
load_dotenv()
API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")
#TESTNET = (os.getenv("BYBIT_TESTNET","true").lower() == "true")


# Endpoint URL
BASE_URL = "https://api.bybit.com"
ORDER_HISTORY_URL = "/v5/order/history"
SERVER_TIME_URL = "/v2/public/time"

# Function to generate the signature
def generate_signature(api_key, api_secret, params):
    # Sort parameters by key
    sorted_params = sorted(params.items())
    query_string = '&'.join([f"{key}={value}" for key, value in sorted_params])
    signature = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    return signature
def get_order_history():
    server_time = get_server_timestamp()  # Get the server's current time in milliseconds
    if not server_time:
        return []

# Function to get the server's current timestamp

# Function to get order history
def get_server_timestamp():
    response = requests.get(BASE_URL + SERVER_TIME_URL)
    
    # Check the HTTP status code to ensure it's a successful request (200 OK)
    if response.status_code == 200:
        try:
            # Attempt to parse the JSON response
            data = response.json()
            if data['retCode'] == 0:
                return data['result']['time']
            else:
                print(f"Error in server response: {data.get('retMsg', 'Unknown error')}")
                return None
        except ValueError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Raw response: {response.text}")
            return None
    else:
        print(f"Error: Received status code {response.status_code} from the server")
        print(f"Raw response: {response.text}")
        return None
    # Parameters for the API request
     # Get the current time and the time two years ago
     
    end_time = server_time  # Current time in milliseconds
    orders = []
    
    # Calculate the timestamp for 2 years ago
    two_years_ago = int((datetime.now() - timedelta(days=365*2)).timestamp() * 1000)
    
    # Loop to fetch data in 7-day increments
    while end_time > two_years_ago:
        start_time = max(end_time - (7 * 24 * 60 * 60 * 1000), two_years_ago)  # 7 days ago or 2 years ago, whichever is earlier
        
        # Parameters for the API request
        params = {
            'api_key': API_KEY,
            'category': 'spot',  # Example: 'linear', 'inverse', or 'spot'
            'symbol': 'FLOCKUSDT',  # Example: 'BTCUSDT', 'ETHUSDT', etc.
            'limit': 50,  # Number of orders to fetch per request
            'startTime': start_time,  # Start time (7 days ago or 2 years ago)
            'endTime': end_time,  # End time (current time)
            'orderStatus': 'Filled',  # Request only filled or partially filled but cancelled orders
            'timestamp': server_time,  # Use server's timestamp in milliseconds
            'recv_window': 5000  # Allow a 5-second tolerance for the timestamp
        }
    
   
        # Generate the signature
        signature = generate_signature(API_KEY, API_SECRET, params)
        params['sign'] = signature

        response = requests.get(BASE_URL + ORDER_HISTORY_URL, params=params)
        data = response.json()

        if data['retCode'] == 0:
            orders.extend(data['result']['list'])  # Add the orders to the list
            next_cursor = data['result'].get('nextPageCursor')
            if next_cursor:
                params['cursor'] = next_cursor  # Set the cursor for the next page
            else:
                break  # Exit if there's no next page
        else:
            print(f"Error: {data.get('retMsg', 'Unknown error')}")
            break

        # Move the time window backwards
        end_time = start_time  # Now the end time becomes the new start time for the next request

    return orders

# Call the function and print the order history
order_history = get_order_history()
if order_history:
    for order in order_history:
        print(order)
else:
    print("No orders found.")