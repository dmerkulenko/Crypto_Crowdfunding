// SPDX-License-Identifier: MIT
pragma solidity ^0.5.0;

import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/release-v2.5.0/contracts/token/ERC721/ERC721Full.sol";

contract CrowdFund is ERC721Full {
    uint256 public contribution_minimum;
    uint256 public goal;
    bool public fundraise_complete_flag = false;
    uint256 public raised = 0;
    address public beneficiary_address;
    //address public return_or_forward_address; //Variable not currently used - possible option to pay forward if an amount is to be refunded
    string tokenURI;
    uint256 public iterator = 0;
    address public contract_deployer_address = msg.sender;
    bool public refundable_flag;
    uint256 public date_stamp;
    uint256 public tip_total = 0;

    constructor(
        uint256 _goal,
        uint256 _contribution_minimum,
        address _beneficiary_address,
        string memory _tokenURI,
        bool _refundable_flag,
        uint256 _date_stamp
    ) public ERC721Full("CrowdfundToken", "CROWD") {
        contribution_minimum = _contribution_minimum;
        goal = _goal;
        beneficiary_address = _beneficiary_address;
        tokenURI = _tokenURI;
        refundable_flag = _refundable_flag;
        date_stamp = _date_stamp;
    }

    struct Test {
        uint256 amount_contributed;
        address contributed_address;
        //string eligible_for_nft; possible additional flag, want to keep track of minimum number of parts in the contract itself, will depend on governance structure of fundraiser
        //string early_bird_draw; possible additional flag, want to keep track of minimum number of parts in the contract itself, will depend on governance structure of fundraiser
    }

    //mapping(uint => Test) public contributorList; took this mapping out in order to use an array instead
    Test[] public contributorList;

    function contribute(uint256 tip_amount) public payable returns (uint256) {
        require(
            msg.value >= contribution_minimum &&
                fundraise_complete_flag == false
        ); //If the contribution limit is reached, offer them an option maybe.
        tip_total = tip_total + tip_amount;
        raised = raised + msg.value - tip_amount; //Update value of amount raised so far
        uint256 token_id = iterator; // returning the token_id to the funciton caller - not sure if needed
        //contributorList[token_id] = Test(backup_option_flag, backup_option_choice, address(uint160(msg.sender))); after switching this to an array, this line is not needed
        contributorList.push(Test(msg.value, address(uint160(msg.sender)))); //record the sender's contribution and address to the contributor list
        if (raised >= goal) {
            // If this function call pushes the total amount raised past the goal, then release the funds and mint the tokens.
            fundraise_complete_flag = true; //Flag the fundraise complete so that the contract can't be called
            address(uint160(beneficiary_address)).transfer(raised); //Send money to the beneficiary
            address(uint160(contract_deployer_address)).transfer(tip_total); //Send tip money to the contract deployer
            for (uint256 i = 0; i < contributorList.length; i++) {
                _mint(contributorList[i].contributed_address, i);
                _setTokenURI(
                    i,
                    string(abi.encodePacked(tokenURI, uintToString(i)))
                );
            } // This for loop mints a token for each person who is listed in the contributor list
        }
        iterator = iterator + 1;
        return token_id;
    }

    //Certain organizations might want a callable refund built in - for example, if the fundraising campaign falls through.
    //The contract deployer is set-up to call this function, hypothetically this could also be a trusted third party like a law firm or audit firm.
    function refund() public payable returns (uint256) {
        require(
            msg.sender == contract_deployer_address && refundable_flag == true
        );
        fundraise_complete_flag = true;
        // Iterate through contributor list and return their contribution money - in this case no tips are paid out.
        for (uint256 i = 0; i < contributorList.length; i++) {
            address(uint160(contributorList[i].contributed_address)).transfer(
                contributorList[i].amount_contributed
            );
        }
        return 0;
    }

    //Function call to release funds after the selected date hypothetically this could release a small amount back to the message sender to cover the gas fees.
    function datePay() public payable returns (uint256) {
        require(date_stamp < now);
        fundraise_complete_flag = true;
        address(uint160(beneficiary_address)).transfer(raised); //Send money to the beneficiary
        address(uint160(contract_deployer_address)).transfer(tip_total); //Send tip money to contract deployer
        for (uint256 i = 0; i < contributorList.length; i++) {
            _mint(contributorList[i].contributed_address, i);
            _setTokenURI(
                i,
                string(abi.encodePacked(tokenURI, uintToString(i)))
            );
        } // This for loop mints a token for each person who is listed in the contributor list
    }

    //got this helper function from: https://ethereum.stackexchange.com/questions/96817/can-a-smart-contract-automatically-generate-tokenuri-based-on-tokenid
    function uintToString(uint256 v) internal pure returns (string memory str) {
        uint256 maxlength = 100;
        bytes memory reversed = new bytes(maxlength);
        uint256 i = 0;
        while (v != 0) {
            uint256 remainder = v % 10;
            v = v / 10;
            reversed[i++] = bytes1(uint8(48 + remainder));
        }
        bytes memory s = new bytes(i);
        for (uint256 j = 0; j < i; j++) {
            s[j] = reversed[i - 1 - j];
        }
        str = string(s);
    }
}
