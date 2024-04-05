from web3 import Web3
from rest_framework import status, response
from .models import ETHAccounts
from django.db import IntegrityError
import json


def gather_eth_accounts_from_ganache():
  provider = Web3.HTTPProvider('http://127.0.0.1:7545')
  w3 = Web3(provider)
  if w3.is_connected():
    accounts = w3.eth.accounts
    for acc in accounts:
      ETHAccounts.objects.get_or_create(public_key=acc)
    return True
  else:
    print("FATAL ERROR: Ganache Connection Failed!!")
    return False

def get_eth_balance(pub_key):
  provider = Web3.HTTPProvider('http://127.0.0.1:7545')
  w3 = Web3(provider)
  if w3.is_connected():
    if w3.is_address(pub_key):
      return w3.from_wei(w3.eth.get_balance(pub_key), 'ether')
    else:
      print("Ganache Error: Invalid Address!!")
      return None
  else:
    print("FATAL ERROR: Ganache Connection Failed!!")
    return None

def transfer_ETH(sender_pub_key, sender_priv_key, reciever_address, ETH_amount):
  # provider = Web3.HTTPProvider('http://127.0.0.1:7545')
  # w3 = Web3(provider)
  # if not w3.is_connected():
  #   return response.Response('Server Error!', status=status.HTTP_500_INTERNAL_SERVER_ERROR)
  # if w3.is_address(sender_pub_key) and w3.is_address(reciever_address):
  #   sender_balance = w3.from_wei(w3.eth.get_balance(sender_pub_key), 'ether')
  #   if sender_balance <= ETH_amount:
  #     return response.Response('Balance Insufficient!', status=status.HTTP_400_BAD_REQUEST)
  #   txn = {
  #     'from': sender_pub_key,
  #     'to': reciever_address,
  #     'value': w3.to_wei(1, 'ether'),
  #     'nonce': w3.eth.get_transaction_count(sender_pub_key),
  #     'maxFeePerGas': 2000000000,
  #     'maxPriorityFeePerGas': 1000000000,
  #     'chainId': 1337,
  #   }
  #   txn.update({'gas': w3.eth.estimate_gas(txn)})
  #   signed_txn = w3.eth.account.sign_transaction(txn, sender_priv_key)
  #   txn = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
  #   txn_json = json.loads(w3.to_json(w3.eth.get_transaction(txn)))
  #   return txn_json
  # else:
  #   return response.Response('Invalid Address!', status=status.HTTP_400_BAD_REQUEST)
  pass
  

