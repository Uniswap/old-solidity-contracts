import pytest
from ethereum import utils as u
import json
import os

"""
    run test with:     python3.6 -m pytest -v
"""

ETH = 10**18
TOKEN = 10**12
EXCHANGE_ABI = os.path.join(os.path.dirname(__file__), '../ABI/exchangeABI.json')

@pytest.fixture
def uni_token(t, contract_tester):
    return contract_tester('Token/UniToken.sol', args=[])

@pytest.fixture
def swap_token(t, contract_tester):
    return contract_tester('Token/SwapToken.sol', args=[])

@pytest.fixture
def uniswap_factory(t, contract_tester):
    return contract_tester('Exchange/UniswapFactory.sol', args=[])

def test_token_to_token(t, uni_token, swap_token, uniswap_factory, contract_tester, assert_tx_failed):
    t.s.mine()
    abi = json.load(open(EXCHANGE_ABI))
    # Create UNI and SWAP token exchanges using uniswap factory
    uni_exchange_address = uniswap_factory.createExchange(uni_token.address)
    uni_exchange = t.ABIContract(t.s, abi, uni_exchange_address)
    swap_exchange_address = uniswap_factory.createExchange(swap_token.address)
    swap_exchange = t.ABIContract(t.s, abi, swap_exchange_address)
    t.s.mine()
    # Mint tokens and approve transferFrom for UNI liquidity provider
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.approve(uni_exchange_address, 10*TOKEN, sender=t.k1)
    # Mint tokens and approve transferFrom for SWAP liquidity provider
    swap_token.mint(t.a2, 20*TOKEN)
    swap_token.approve(swap_exchange_address, 20*TOKEN, sender=t.k2)
    # Mint tokens and approve transferFrom for UNI to SWAP buyer
    uni_token.mint(t.a3, 10*TOKEN)
    uni_token.approve(uni_exchange_address, 10*TOKEN, sender=t.k3)
    # UNI provider initializes the exchange with 5 eth and 10 tokens
    uni_exchange.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    # SWAP provider initializes the exchange with 5 eth and 10 tokens
    swap_exchange.initializeExchange(20*TOKEN, value=5*ETH, sender=t.k2)
    t.s.mine()
    # BUYER buys SWAP tokens with UNI
    #uni_exchange.tokenToEthToTunnel(swap_exchange_address, 2*TOKEN, sender=t.k3)
