from fastapi import Request
import requests
import os


class BabelAPIClient:
    def __init__(self, request: Request):

        try:
            first_tkn = request.headers.get("Authorization")
            babel_tkn = request.headers.get("xx-Authorization")

            self.base_url = os.getenv("BABEL_API_URL", "http://localhost:8888")

            self.headers = {
                **request.headers,
                "Authorization": babel_tkn,
                "xx-Authorization": first_tkn,
            }
        except Exception as ex:
            print(ex)

    def ping(self):
        url = f"{self.base_url}/health"
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        return "pong"

    def consume(self, action):
        url = f"{self.base_url}/permission/1/{action}?consume=true"
        try:
            requests.get(url, headers=self.headers)
        except Exception as ex:
            print("consume Error: {}".format(ex))
