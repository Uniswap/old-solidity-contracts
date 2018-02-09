import pytest
from ethereum import utils as u

"""
    run test with:     pytest -v
"""

# Constants
ETH = 10**18
TOKEN = 10**18

@pytest.fixture
def uni_token(t, contract_tester):
    return contract_tester('Token/UniToken.sol', args=[])

@pytest.fixture
def uniswap_exchange(t, contract_tester, uni_token):
    return contract_tester('Exchange/UniswapExchange.sol', args=[uni_token.address])

def test_exchange_initial_state(t, uni_token, uniswap_exchange, contract_tester, assert_tx_failed):
    assert uniswap_exchange.FEE_RATE() == 500
    assert uniswap_exchange.ethInMarket() == 0
    assert uniswap_exchange.tokensInMarket() == 0
    assert uniswap_exchange.invariant() == 0
    assert uniswap_exchange.ethFees() == 0
    assert uniswap_exchange.tokenFees() == 0
    assert u.remove_0x_head(uniswap_exchange.tokenAddress()) == uni_token.address.hex()
    assert uniswap_exchange.totalShares() == 0

def test_initialize_exchange(t, uni_token, uniswap_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.approve(uniswap_exchange.address, 10*TOKEN, sender=t.k1)
    # Starting balances of PROVIDER (t.a1)
    assert t.s.head_state.get_balance(t.a1) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a1) == 10000000000000000000
    # PROVIDER initializes exchange
    uniswap_exchange.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    # Updated balances of UNI exchange
    assert uniswap_exchange.invariant() == 10*TOKEN*5*ETH
    assert uniswap_exchange.ethInMarket() == 5*ETH
    assert uniswap_exchange.tokensInMarket() == 10*TOKEN
    assert uni_token.balanceOf(uniswap_exchange.address) == 10*TOKEN
    assert uniswap_exchange.totalShares() == 1000
    assert t.s.head_state.get_balance(uniswap_exchange.address) == 5*ETH
    # Final balances of PROVIDER
    assert t.s.head_state.get_balance(t.a1) == 1000000000000000000000000000000 - 5*ETH
    assert uni_token.balanceOf(t.a1) == 0
