import os
import json
from web3 import Web3
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import datetime

load_dotenv()

w3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_PROVIDER_URI")))


df = pd.read_csv("example_database.csv", header=0, index_col=None, squeeze=False)
df.set_index("contract_address", inplace=True)

dictionary = df.to_dict("index")

name_to_contract_dictionary = {}
for i in dictionary.keys():
    name_to_contract_dictionary[dictionary[i]["beneficiary_name"]] = i


def load_contract():

    # Load the contract ABI
    with open(Path("./contracts/crowdfund_abi.json")) as f:
        crowdfund_abi = json.load(f)

    # Set the contract address (this is the address of the deployed contract)
    contract_address = dictionary.keys()
    contracts = {}
    # Get the contract
    counter = 0
    for i in contract_address:
        #print(i)
        #print(crowdfund_abi)
        #break
        contracts[i] = w3.eth.contract(address=i, abi=crowdfund_abi)
        counter += 1
    return contracts


# Load the contract
contract = load_contract()
# contract_names = [d["beneficiary_name"] for d in contract]

# 1. Project Title
st.title("Contribute to a contract")

# 2. Select a contract
accounts = w3.eth.accounts
selected_name = st.selectbox(
    "Select a contract", options=name_to_contract_dictionary.keys()
)
selected = name_to_contract_dictionary[selected_name]

# 3. Select a Contributing Wallet
address = st.selectbox("Select your contributing wallet", options=accounts)

# 4A. USD dollar amount

import requests

url = "https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD&api_key=b13fe0d24e23abff0b6054424874351e7985fcd73461de3d78552418ba30f3e7"

response = requests.get(url).json()

price = response["USD"]

def convert_to_USD(x) :
    somme = price*x
    return somme

def convert_to_ETH(x) :
    s = x/price
    somme = round(s,6) 
    return somme

#min_value_wei= int(dictionary[selected]["contribution_minimum"])
#min_value_eth = min_value_wei/1000000000000000000
#min_value_usd = convert_to_USD(min_value_eth)



usd_amount = st.number_input(
    "Select an amount to contribute in USD",
    min_value = int(dictionary[selected]["usd_minimum"])
    )

# 4B. ETH amount = contibution_amount Convert USD to wei

if usd_amount>0:
    converted = convert_to_ETH(usd_amount)
    st.write("Your contribution in ETH: ")
    st.write(converted)
    converted_to_wei = converted * 1000000000000000000
    st.write("Your contribution in wei: ")
    st.write(converted_to_wei)
else:
    ()

# 5. Tip Amount

tip_amount = int(
    st.slider("Tip Our Crowdfunding Project %", min_value=0.0, max_value=100.0, format="%g percent")
)
# 6. Total Breakdown

total = int(converted_to_wei * (1+tip_amount/100))
with st.sidebar:
    st.markdown("**Here's Your Contribution Breakdown:**")
    st.markdown("Contribution to " + str(selected_name) + " project:" + str(converted_to_wei)+ " wei")
    st.markdown("Crowdfunding Tip: " + str(tip_amount)+ " %")
    st.markdown("**Total: " + str(total) + " wei**")

selected_contract = contract[selected]
today = int(datetime.datetime.today().timestamp())
if st.button("Contribute"):
    completion_flag = selected_contract.functions.fundraise_complete_flag().call()
    if completion_flag:
        st.write("Fundraising is complete, you cannot contribute to this fundraiser!")
    elif today > int(dictionary[selected]["target_date"]):
        st.write(
            "Fundraising date has passed, you cannot contribute to this fundraiser!"
        )
    else:
        tx_hash = selected_contract.functions.contribute(int(total - converted_to_wei)).transact(
            {"from": address, "gas": 1000000, "value": total}
        )
        receipt = w3.eth.waitForTransactionReceipt(tx_hash)
        st.write("Transaction receipt mined:")
        st.write(dict(receipt))
    st.write(
        "Contract has raised: "
        + str(selected_contract.functions.raised().call())
        + " so far")
    st.balloons()
st.markdown("---")