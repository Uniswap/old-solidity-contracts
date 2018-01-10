import pytest
from ethereum import utils as u

"""
    run test with:     python3.6 -m pytest -v
"""

# Constants
ETH = 10**18
TOKEN = 10**12

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
    assert uniswap_exchange.ethFeePool() == 0
    assert uniswap_exchange.tokenFeePool() == 0
    assert u.remove_0x_head(uniswap_exchange.tokenAddress()) == uni_token.address.hex()
    assert uniswap_exchange.totalShares() == 0
    assert uniswap_exchange.lastFeeDistribution() == 0

def test_initialize_exchange(t, uni_token, uniswap_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.approve(uniswap_exchange.address, 10*TOKEN, sender=t.k1)
    # Assert starting ETH balance of test account
    assert t.s.head_state.get_balance(t.a1) == 1000000000000000000000000000000
    # PROVIDER initializes exchange
    uniswap_exchange.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    # Updated state of UNI exchange
    assert uniswap_exchange.invariant() == 10*TOKEN*5*ETH
    assert uniswap_exchange.ethInMarket() == 5*ETH
    assert uniswap_exchange.tokensInMarket() == 10*TOKEN
    assert uni_token.balanceOf(uniswap_exchange.address) == 10*TOKEN
    assert uniswap_exchange.totalShares() == 1000
    assert t.s.head_state.get_balance(uniswap_exchange.address) == 5*ETH
    # Assert final ETH balance of test account
    assert t.s.head_state.get_balance(t.a1) == 1000000000000000000000000000000 - 5*ETH

def test_eth_to_tokens(t, uni_token, uniswap_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.approve(uniswap_exchange.address, 10*TOKEN, sender=t.k1)
    # PROVIDER initializes exchange
    uniswap_exchange.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    # Starting balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a2) == 0
    # BUYER converts ETH to UNI
    uniswap_exchange.ethToTokens(1, timeout, value=1*ETH, sender=t.k2)
    INVARIANT = 5*ETH*10*TOKEN
    fee = 1*ETH/500
    new_market_eth = 5*ETH + 1*ETH - fee
    new_market_tokens = int(INVARIANT/new_market_eth)
    purchased_tokens = 10*TOKEN - new_market_tokens
    # Updated balances of UNI exchange
    assert uniswap_exchange.ethFeePool() == fee
    assert uniswap_exchange.ethInMarket() == new_market_eth
    assert t.s.head_state.get_balance(uniswap_exchange.address) == new_market_eth + fee
    assert uniswap_exchange.tokensInMarket() == new_market_tokens
    assert uni_token.balanceOf(uniswap_exchange.address) == new_market_tokens
    # Final balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000 - 1*ETH
    assert uni_token.balanceOf(t.a2) == purchased_tokens
    # Min tokens = 0
    assert_tx_failed(t, lambda: uniswap_exchange.ethToTokens(0, timeout, value=1*ETH, sender=t.k2))
    # Purchased tokens < min tokens
    assert_tx_failed(t, lambda: uniswap_exchange.ethToTokens(purchased_tokens + 1, timeout, value=1*ETH, sender=t.k2))
    # Timeout = 0
    assert_tx_failed(t, lambda: uniswap_exchange.ethToTokens(1, 0, value=1*ETH, sender=t.k2))
    # Timeout < now
    assert_tx_failed(t, lambda: uniswap_exchange.ethToTokens(1, timeout - 301, value=1*ETH, sender=t.k2))
    # msg.value = 0
    assert_tx_failed(t, lambda: uniswap_exchange.ethToTokens(1, timeout, value=0, sender=t.k2))

def test_tokens_to_eth(t, uni_token, uniswap_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.mint(t.a2, 2*TOKEN)
    uni_token.approve(uniswap_exchange.address, 10*TOKEN, sender=t.k1)
    uni_token.approve(uniswap_exchange.address, 2*TOKEN, sender=t.k2)
    # PROVIDER initializes exchange
    uniswap_exchange.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    INVARIANT = 5*ETH*10*TOKEN
    # Starting balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a2) == 2*TOKEN
    # BUYER converts UNI to ETH
    uniswap_exchange.tokenToEth(2*TOKEN, 1, timeout, sender=t.k2)
    # UNI exchange state changes
    fee = 2*TOKEN/500;
    new_market_tokens = 10*TOKEN + 2*TOKEN - fee
    new_market_eth = int(INVARIANT/new_market_tokens)
    purchased_eth = 5*ETH - new_market_eth
    # Updated balances of UNI exchange
    assert uniswap_exchange.tokenFeePool() == fee
    assert uniswap_exchange.tokensInMarket() == new_market_tokens
    assert uni_token.balanceOf(uniswap_exchange.address) == new_market_tokens + fee
    assert uniswap_exchange.ethInMarket() == new_market_eth - 429         # rounding error of 429 wei
    assert t.s.head_state.get_balance(uniswap_exchange.address) == new_market_eth - 429
    # Final balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000 + purchased_eth + 429
    assert uni_token.balanceOf(t.a2) == 0
    # Tokens sold = 0
    assert_tx_failed(t, lambda: uniswap_exchange.tokenToEth(0, 1, timeout, sender=t.k2))
    # Tokens sold > balances[msg.sender]
    assert_tx_failed(t, lambda: uniswap_exchange.tokenToEth(3*TOKEN, 1, timeout, sender=t.k2))
    # Min eth = 0
    assert_tx_failed(t, lambda: uniswap_exchange.tokenToEth(2*TOKEN, 0, timeout, sender=t.k2))
    # Purchased ETH < min ETH
    assert_tx_failed(t, lambda: uniswap_exchange.tokenToEth(2*TOKEN, purchased_eth + 1, timeout, sender=t.k2))
    # Timeout = 0
    assert_tx_failed(t, lambda: uniswap_exchange.tokenToEth(2*TOKEN, 1, 0, sender=t.k2))
    # Timeout < now
    assert_tx_failed(t, lambda: uniswap_exchange.tokenToEth(2*TOKEN, 1, timeout - 301, sender=t.k2))

def test_fallback_eth_to_tokens(t, uni_token, uniswap_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.approve(uniswap_exchange.address, 10*TOKEN, sender=t.k1)
    # PROVIDER initializes exchange
    uniswap_exchange.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    INVARIANT = 5*ETH*10*TOKEN
    # Starting balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a2) == 0
    t.s.mine();
    # BUYER converts ETH to UNI
    STARTGAS=90000
    t.s.tx(to=uniswap_exchange.address, startgas=STARTGAS, value=1*ETH, sender=t.k2)
    fee = 1*ETH/500
    new_market_eth = 5*ETH + 1*ETH - fee
    new_market_tokens = int(INVARIANT/new_market_eth)
    purchased_tokens = 10*TOKEN - new_market_tokens
    # Updated balances of UNI exchange
    assert uniswap_exchange.ethFeePool() == fee
    assert uniswap_exchange.ethInMarket() == new_market_eth
    assert t.s.head_state.get_balance(uniswap_exchange.address) == new_market_eth + fee
    assert uniswap_exchange.tokensInMarket() == new_market_tokens
    assert uni_token.balanceOf(uniswap_exchange.address) == new_market_tokens
    # Final balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000 - 1*ETH
    assert uni_token.balanceOf(t.a2) == purchased_tokens
    # msg.value = 0
    assert_tx_failed(t, lambda: t.s.tx(to=uniswap_exchange.address, startgas=STARTGAS, sender=t.k2))
    # not enough gas
    assert_tx_failed(t, lambda: t.s.tx(to=uniswap_exchange.address, startgas=21000, value=1*ETH, sender=t.k2))
