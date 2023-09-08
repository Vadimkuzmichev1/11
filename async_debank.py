from concurrent.futures import ThreadPoolExecutor

import json
import os

import requests

from key import debank_api

url = 'https://pro-openapi.debank.com/v1/user/all_history_list'
headers = {
    'accept': 'application/json',
    'AccessKey': debank_api
}


def make_params(start_time, address):
    params = {
        'id': address,
        'start_time': start_time,
        'page_count': 20
    }
    return params

def debank(wallet, counter):
    print(f"{counter} - {wallet}")

    duplicate = False
    file_path = f'data/{wallet}.json'

    if os.path.isfile(file_path):

        with open(file_path, 'r') as file:
            wallet_data = json.load(file)
        len_transaction = len(wallet_data)
        start_time = 0
        id_set = set(transaction['id'] for transaction in wallet_data)
        new_wallet_data = []
        new_wallet_data.extend(wallet_data)
        while not duplicate:
            response = requests.get(url, headers=headers, params=make_params(start_time, wallet))
            data = response.json().get("history_list", [])

            if data:
                for new_transaction in data:
                    if new_transaction["id"] not in id_set:
                        new_wallet_data.append(new_transaction)
                    else:
                        duplicate = True
            else:
                break
            start_time = int(data[-1]['time_at']) - 1

        sorted_list = sorted(new_wallet_data, key=lambda x: x['time_at'])

        with open(file_path, 'w') as file:
            json.dump(sorted_list, file)

        if len(new_wallet_data) - len_transaction:
            print(f"Было транзакций {len_transaction} - стало {len(new_wallet_data)} прибавили {len(new_wallet_data) - len_transaction}")

    else:
        start_time = 0
        response = requests.get(url, headers=headers, params=make_params(start_time, wallet))
        wallet_data = response.json().get("history_list", [])

        if wallet_data:
            start_time = int(wallet_data[-1]['time_at']) - 1
        while True:
            response = requests.get(url, headers=headers, params=make_params(start_time, wallet))
            data = response.json().get("history_list", [])
            if data:
                wallet_data.extend(data)
                start_time = int(wallet_data[-1]['time_at']) - 1
            else:
                break
        sorted_list = sorted(wallet_data, key=lambda x: x['time_at'])
        with open(file_path, 'w') as file:
            json.dump(sorted_list, file)
        print(f"Добавили {len(sorted_list)} транзакций в новый файл")


def main():
    if not os.path.exists("result"):
        os.mkdir("result")
    if not os.path.exists("data"):
        os.mkdir("data")

    with open("wallets.txt", "r") as f:
        wallets = [row.strip() for row in f if row.strip()]
    counter = len(wallets)
    with ThreadPoolExecutor(max_workers=10) as executor:
        for wallet in wallets:
            executor.submit(debank, wallet, counter)
            counter -= 1
main()