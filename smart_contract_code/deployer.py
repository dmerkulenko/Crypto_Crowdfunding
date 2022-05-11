#from solcx import compile_standard, install_solc
import json
from web3 import Web3
import os
from web3 import Web3
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import csv
import datetime

with open("contracts/crowdfund_abi.json") as file:
    abi = json.load(file)
with open("contracts/bytecode.txt") as file:
    bytecode = json.load(file)

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))
chain_id = 1337

address = "0xB2e5649c228Aa2281323E0a0B3BfC70382744F1D"
private_key = "fa25b78324f59d922e524c734c28e04e48da045920f3c8ec3ddd46bc36d88d21"

# Create the contract in Python
new_contract = w3.eth.contract(abi=abi, bytecode=bytecode)
# Get the number of latest transaction
st.title("Create a contract")
organization_name = st.text_input("Enter your organization's name")
usd_amount = int(st.number_input("Select your fundraising goal in USD"))

#Convert from USD to ETH and then to wei
import requests

url = "https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD&api_key=b13fe0d24e23abff0b6054424874351e7985fcd73461de3d78552418ba30f3e7"

response = requests.get(url).json()

price = response["USD"]

def convert_to_ETH(x) :
    s = x/price
    somme = round(s,6) 
    return somme

if usd_amount>0:
    converted = convert_to_ETH(usd_amount)
    st.write("Your foundraising goal in ETH: ")
    st.write(converted)
    goal_amount = int(converted * 1000000000000000000)
    st.write("Your foundraising goal in wei: ")
    st.write(goal_amount)
else:
    ()
usd_minimum = int(st.number_input("Select the minimum amount to contribute in USD"))
if usd_minimum>0:
    minimum_converted = convert_to_ETH(usd_minimum)
    st.write("Your contribution minimum in ETH: ")
    st.write(minimum_converted)
    contribution_minimum= int(minimum_converted * 1000000000000000000)
    st.write("Your foundraising goal in wei: ")
    st.write(contribution_minimum)
else:
    ()
beneficiary_address = st.text_input("Paste your beneficiary address")
uri = st.text_input("Paste your URI")
end_date_input = st.date_input("Enter your end date")
end_date = int(
    datetime.datetime.combine(end_date_input, datetime.datetime.min.time()).timestamp()
)
print(type(end_date))
print(end_date)
refund_flag = st.checkbox("Do you want to be able to refund the contract?")
if st.button("Deploy Contract"):
    nonce = w3.eth.getTransactionCount(address)
    # build transaction
    transaction = new_contract.constructor(
        goal_amount,
        contribution_minimum,
        beneficiary_address,
        uri,
        refund_flag,
        end_date,
    ).buildTransaction(
        {
            "chainId": chain_id,
            "gasPrice": w3.eth.gas_price,
            "from": address,
            "nonce": nonce,
        }
    )
    # Sign the transaction
    sign_transaction = w3.eth.account.sign_transaction(
        transaction, private_key=private_key
    )
    st.write("Deploying Contract!")
    # Send the transaction
    transaction_hash = w3.eth.send_raw_transaction(sign_transaction.rawTransaction)
    #Wait for the transaction to be mined, and get the transaction receipt
    st.write("Waiting for transaction to finish...")
    transaction_receipt = w3.eth.wait_for_transaction_receipt(transaction_hash)
    st.write(f"Done! Contract deployed to {transaction_receipt.contractAddress}")
    with open("example_database.csv", "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                transaction_receipt.contractAddress,
                beneficiary_address,
                organization_name,
                goal_amount,
                contribution_minimum,
                uri,
                end_date,
                usd_minimum
            ]
        )
        file.close()