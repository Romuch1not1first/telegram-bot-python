import requests

# requests yobit
class exchange:
    @staticmethod
    def get_currency(currency):
        url = f'https://yobit.net/api/2/{currency}/ticker'
        r = requests.get(url)
        data = r.json()
        return data