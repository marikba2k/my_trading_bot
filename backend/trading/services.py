from django.contrib.auth.models import User
from pybit.unified_trading import HTTP
from pybit.exceptions import InvalidRequestError
from accounts.models import ApiCredential

class MissingCredentials(Exception): ...
class InvalidCredentials(Exception): ...

def get_user_session(user: User, is_testnet: bool = True) -> HTTP:
    """
    Returns a configured PyBit HTTP session for the given user.
    Pulls encrypted creds from ApiCredential (is_testnet=True by default).
    """
    cred = ApiCredential.objects.filter(user=user, is_testnet=is_testnet).first()
    if not cred:
        raise MissingCredentials("No saved Bybit credentials for this user (testnet).")
    api_key = cred.api_key.strip()
    api_secret = cred.get_secret().strip()
    try:
        return HTTP(api_key=api_key, api_secret=api_secret, testnet=is_testnet)
    except Exception as e:
        raise InvalidCredentials(str(e))
