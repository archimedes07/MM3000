import aiohttp
import time
import hmac
import hashlib
import json
from dataclasses import dataclass

@dataclass
class OrderResponse:
    success: bool = False
    order_id: str = ""
    error_message: str = ""
    execution_time_ms: float = 0.0
    status: str = ""
    executed_qty: float = 0.0
    price: float = 0.0

class OrderExecutor:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.mexc.com/api/v3"

    def _generate_timestamp(self) -> int:
        return int(time.time() * 1000)

    def _generate_signature(self, query_string: str) -> str:
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    async def _send_request(self, method: str, path: str, params: dict) -> OrderResponse:
        response = OrderResponse()
        params["timestamp"] = self._generate_timestamp()
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        signature = self._generate_signature(query_string)
        url = f"{self.base_url}{path}?{query_string}&signature={signature}"
        headers = {
            "X-MEXC-APIKEY": self.api_key,
            "Content-Type": "application/json"
        }

        start = time.time()
        async with aiohttp.ClientSession() as session:
            try:
                if method.upper() == "POST":
                    async with session.post(url, headers=headers) as resp:
                        text = await resp.text()
                elif method.upper() == "DELETE":
                    async with session.delete(url, headers=headers) as resp:
                        text = await resp.text()
                elif method.upper() == "GET":
                    async with session.get(url, headers=headers) as resp:
                        text = await resp.text()
                else:
                    response.success = False
                    response.error_message = f"Unsupported HTTP method {method}"
                    return response

                response.execution_time_ms = (time.time() - start) * 1000

                if resp.status == 200:
                    response.success = True
                    data = json.loads(text)
                    response.order_id = data.get("orderId", "")
                    response.status = data.get("status", "")
                    response.price = float(data.get("price", 0))
                    response.executed_qty = float(data.get("executedQty", 0))
                else:
                    response.success = False
                    response.error_message = text

            except Exception as e:
                response.success = False
                response.error_message = str(e)

        return response

    async def place_buy_limit_order(self, symbol: str, price: float, quantity: float) -> OrderResponse:
        params = {"symbol": symbol, "side": "BUY", "type": "LIMIT", "price": price, "quantity": quantity}
        return await self._send_request("POST", "/order", params)

    async def place_sell_limit_order(self, symbol: str, price: float, quantity: float) -> OrderResponse:
        params = {"symbol": symbol, "side": "SELL", "type": "LIMIT", "price": price, "quantity": quantity}
        return await self._send_request("POST", "/order", params)

    async def cancel_order(self, symbol: str, order_id: str) -> OrderResponse:
        params = {"symbol": symbol, "orderId": order_id}
        return await self._send_request("DELETE", "/order", params)

    async def get_order_status(self, symbol: str, order_id: str) -> OrderResponse:
        params = {"symbol": symbol, "orderId": order_id}
        return await self._send_request("GET", "/order", params)
