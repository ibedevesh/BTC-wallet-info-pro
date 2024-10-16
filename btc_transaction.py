import requests
import json
from datetime import datetime

def get_address_info(address, offset=0, limit=50):
    url = f"https://blockchain.info/rawaddr/{address}?offset={offset}&limit={limit}"
    response = requests.get(url)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return None

def satoshi_to_btc(satoshi):
    return satoshi / 1e8

def safe_get(dct, *keys, default=None):
    for key in keys:
        try:
            dct = dct[key]
        except (KeyError, TypeError):
            return default
    return dct if dct is not None else default

def print_address_info(address):
    offset = 0
    limit = 50
    max_transactions = 500  # Maximum number of transactions to process
    sent_transactions = []
    received_transactions = []
    total_processed = 0

    while total_processed < max_transactions:
        address_data = get_address_info(address, offset, limit)
        if not address_data or 'txs' not in address_data:
            break

        for tx in address_data['txs']:
            total_processed += 1
            time = datetime.fromtimestamp(tx['time']).strftime('%Y-%m-%d %H:%M:%S')
            
            inputs = tx.get('inputs', [])
            is_sending = any(safe_get(input, 'prev_out', 'addr') == address for input in inputs)
            
            if is_sending:
                amount_sent = sum(safe_get(out, 'value', default=0) for out in tx['out'] if safe_get(out, 'addr') != address)
                recipients = [safe_get(out, 'addr') for out in tx['out'] if safe_get(out, 'addr') and safe_get(out, 'addr') != address]
                sent_transactions.append((time, satoshi_to_btc(amount_sent), recipients))
            else:
                amount_received = sum(safe_get(out, 'value', default=0) for out in tx['out'] if safe_get(out, 'addr') == address)
                senders = [safe_get(input, 'prev_out', 'addr') for input in inputs if safe_get(input, 'prev_out', 'addr')]
                received_transactions.append((time, satoshi_to_btc(amount_received), senders))

        if len(address_data['txs']) < limit:
            break
        offset += limit

    # Print address info
    print(f"Address: {address}")
    print(f"Final Balance: {satoshi_to_btc(address_data['final_balance']):.8f} BTC")
    print(f"Total Received: {satoshi_to_btc(address_data['total_received']):.8f} BTC")
    print(f"Total Sent: {satoshi_to_btc(address_data['total_sent']):.8f} BTC")
    print(f"Number of Transactions: {address_data['n_tx']}")
    print(f"\nTotal transactions processed: {total_processed}")

    print("\nRecent Outgoing Transactions:")
    if sent_transactions:
        for time, amount, recipients in sent_transactions[:10]:
            print(f"Sent: {amount:.8f} BTC on {time}")
            print(f"  To: {', '.join(str(r) for r in recipients[:3])}{'...' if len(recipients) > 3 else ''}")
            print()
    else:
        print("No outgoing transactions found in the processed history.")

    print("\nRecent Incoming Transactions:")
    for time, amount, senders in received_transactions[:10]:
        print(f"Received: {amount:.8f} BTC on {time}")
        print(f"  From: {', '.join(str(s) for s in senders[:3])}{'...' if len(senders) > 3 else ''}")
        print()

def main():
    address = input("Enter a Bitcoin address: ")
    print_address_info(address)

if __name__ == "__main__":
    main()
