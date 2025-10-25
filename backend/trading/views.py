from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from pybit.exceptions import InvalidRequestError
from .services import get_user_session, MissingCredentials

class KeyInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        try:
            s = get_user_session(request.user, is_testnet=True)
            info = s.get_api_key_information()
            return Response({"ok": True, "info": info})
        except MissingCredentials as e:
            return Response({"ok": False, "error": str(e)}, status=400)
        except InvalidRequestError as e:
            return Response({"ok": False, "error": str(e)}, status=400)

class WalletBalanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        accountType = request.GET.get("accountType", "UNIFIED")
        # guardrail: only allow known types
        if accountType not in ("UNIFIED", "SPOT", "CONTRACT"):
            return Response({"ok": False, "error": "Invalid accountType"}, status=400)
        try:
            s = get_user_session(request.user, is_testnet=True)
            data = s.get_wallet_balance(accountType=accountType)
            return Response({"ok": True, "accountType": accountType, "data": data})
        except MissingCredentials as e:
            return Response({"ok": False, "error": str(e)}, status=400)
        except InvalidRequestError as e:
            return Response({"ok": False, "error": str(e)}, status=400)

class OpenOrdersView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        # defaults for testnet linear futures
        symbol   = request.GET.get("symbol", "BTCUSDT")
        category = request.GET.get("category", "linear")  # linear | spot | inverse
        if category not in ("linear", "spot", "inverse"):
            return Response({"ok": False, "error": "Invalid category"}, status=400)
        try:
            s = get_user_session(request.user, is_testnet=True)
            data = s.get_open_orders(category=category, symbol=symbol)
            return Response({"ok": True, "category": category, "symbol": symbol, "data": data})
        except MissingCredentials as e:
            return Response({"ok": False, "error": str(e)}, status=400)
        except InvalidRequestError as e:
            return Response({"ok": False, "error": str(e)}, status=400)
