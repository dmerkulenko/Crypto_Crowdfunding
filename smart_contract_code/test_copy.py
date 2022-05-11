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
        contracts[i] = w3.eth.contract(address=i, abi=crowdfund_abi)
        counter += 1
    return contracts


# Load the contract
contract = load_contract()
# contract_names = [d["beneficiary_name"] for d in contract]
st.title("Contribute to a contract")
accounts = w3.eth.accounts
selected_name = st.selectbox(
    "Select a contract", options=name_to_contract_dictionary.keys()
)
selected = name_to_contract_dictionary[selected_name]
address = st.selectbox("Select your contributing wallet", options=accounts)

contribution_amount = int(
    st.number_input(
        "Select an amount to contribute",
        min_value=dictionary[selected]["contribution_minimum"],
    )
)
tip_amount = int(st.number_input("Select an amount to tip"))
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
        tx_hash = selected_contract.functions.contribute(tip_amount).transact(
            {"from": address, "gas": 1000000, "value": contribution_amount + tip_amount}
        )
        receipt = w3.eth.waitForTransactionReceipt(tx_hash)
        st.write("Transaction receipt mined:")
        st.write(dict(receipt))
    st.write(
        "Contract has raised: "
        + str(selected_contract.functions.raised().call())
        + " so far"
    )
st.markdown("---")
