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

def test_uniswap_factory(t, uni_token, swap_token, uniswap_factory, contract_tester, assert_tx_failed):
    t.s.mine()
    # Create UNI token exchange
    uni_exchange_address = uniswap_factory.createExchange(uni_token.address)
    start_time = t.s.head_state.timestamp
    assert uniswap_factory.getExchangeCount() == 1
    assert uniswap_factory.doesExchangeExist(uni_token.address) == True
    assert uni_exchange_address == uniswap_factory.tokenExchangeLookup(uni_token.address)
    abi = json.load(open(EXCHANGE_ABI))
    uni_token_exchange = t.ABIContract(t.s, abi, uni_exchange_address)
    # Test UNI token exchange initial state
    assert uni_token_exchange.FEE_RATE() == 500
    assert uni_token_exchange.ethInMarket() == 0
    assert uni_token_exchange.tokensInMarket() == 0
    assert uni_token_exchange.invariant() == 0
    assert uni_token_exchange.ethFeePool() == 0
    assert uni_token_exchange.tokenFeePool() == 0
    assert u.remove_0x_head(uni_token_exchange.tokenAddress()) == uni_token.address.hex()
    assert uni_token_exchange.totalShares() == 0
    assert uni_token_exchange.lastFeeDistribution() == start_time
    t.s.mine()
    # Create SWAP token exchange
    swap_exchange_address = uniswap_factory.createExchange(swap_token.address)
    assert uniswap_factory.getExchangeCount() == 2
    assert uniswap_factory.doesExchangeExist(swap_token.address) == True
    assert swap_exchange_address == uniswap_factory.tokenExchangeLookup(swap_token.address)
    swap_token_exchange = t.ABIContract(t.s, abi, swap_exchange_address)
    # create exchange fails if sent ether
    assert_tx_failed(t, lambda: uniswap_factory.createExchange(uni_token.address, value=10))
    # create exchange fails if parameters are missing or empty
    assert_tx_failed(t, lambda: uniswap_factory.createExchange())
    assert_tx_failed(t, lambda: uniswap_factory.createExchange('0000000000000000000000000000000000000000'))
