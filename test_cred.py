from pybit.unified_trading import HTTP
import os
from dotenv import load_dotenv
load_dotenv()

# def checkCredential():
#     sess = HTTP(testnet=False,
#             api_key=os.getenv("BYBIT_API_KEY","").strip(),
#             api_secret=os.getenv("BYBIT_API_SECRET","").strip())
#     api_key_info = sess.get_api_key_information()
#     for i in api_key_info:
#         if(isinstance(api_key_info[i], dict)):
#             for j in api_key_info[i]:
#                 print(f"{i} - {j}: {api_key_info[i][j]}")
#         else:
#             print(f"{i} : {api_key_info[i]}")
    
    
def checkBalance():
    print(os.getenv("BYBIT_API_KEY"))
    print(os.getenv("BYBIT_API_SECRET"))
    s = HTTP(api_key=os.getenv("BYBIT_API_KEY"), api_secret=os.getenv("BYBIT_API_SECRET"), testnet=True, demo = True)
    print(s.get_wallet_balance(accountType="UNIFIED"))
    

import os, time, hmac, hashlib, requests
from dotenv import load_dotenv
from pybit.unified_trading import HTTP
from pybit.exceptions import InvalidRequestError

load_dotenv()

API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")

def show_env():
    print("API_KEY repr:", repr(API_KEY), "len:", 0 if API_KEY is None else len(API_KEY))
    print("API_SECRET present:", API_SECRET is not None, "len:", 0 if API_SECRET is None else len(API_SECRET))
    assert API_KEY and API_SECRET, "Missing BYBIT_API_KEY or BYBIT_API_SECRET"
    # reveal whitespace or BOM
    assert API_KEY == API_KEY.strip(), "Whitespace/BOM around BYBIT_API_KEY"
    assert API_SECRET == API_SECRET.strip(), "Whitespace/BOM around BYBIT_API_SECRET"

def try_pybit():
    s = HTTP(api_key=API_KEY.strip(), api_secret=API_SECRET.strip(), testnet=True)
    print("Public ping:", s.get_server_time())  # should succeed
    try:
        print("Wallet UNIFIED:", s.get_wallet_balance(accountType="UNIFIED"))
    except InvalidRequestError as e:
        print("PyBit signed call error:", e)

def try_manual():
    url = "https://api-testnet.bybit.com/v5/user/query-api"
    ts = str(int(time.time()*1000))
    recv = "5000"
    payload = ""  # GET, no body
    sign = hmac.new(API_SECRET.strip().encode(), (ts + API_KEY.strip() + recv + payload).encode(), hashlib.sha256).hexdigest()
    headers = {
        "X-BAPI-API-KEY": API_KEY.strip(),
        "X-BAPI-SIGN": sign,
        "X-BAPI-TIMESTAMP": ts,
        "X-BAPI-RECV-WINDOW": recv,
        "Content-Type": "application/json",
    }
    r = requests.get(url, headers=headers, timeout=15)
    print("Manual status:", r.status_code)
    print("Manual body:", r.text)

def test():
    print(API_KEY)
    print(API_SECRET)
    session = HTTP(api_key=API_KEY, api_secret=API_SECRET, testnet=True, demo = True)
    # Ping Bybit with an authenticated call to make sure its working
    try:
        response = session.get_account_info()
        print("✅ API keys are working!")
        print("Account Info:", response.get('retMsg'))
    except Exception as e:
        print("❌ Failed to authenticate. Please check your API keys.")
        print("Error:", e) 

test()
checkBalance()



