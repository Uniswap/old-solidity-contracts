import pytest
import math
from ethereum import utils as u

"""
    run test with:     python3.6 -m pytest
"""

ETH = 10**18
TOKEN = 10**12

@pytest.fixture
def uni_token(t, contract_tester):
    return contract_tester('Token/UniToken.sol', args=[])

@pytest.fixture
def uniswap_multi(t, contract_tester, uni_token):
    return contract_tester('Exchange/UniswapMultipleProviders.sol', args=[uni_token.address])

def test_token(t, uni_token, contract_tester, assert_tx_failed):
    TOKEN_BALANCE_A1 = 100*10**12
    TOKEN_BALANCE_A2 = 200*10**12
    # Test Initial State
    assert uni_token.name().decode("utf-8") == 'UNI Test Token'
    assert uni_token.symbol().decode("utf-8") == 'UNI'
    assert uni_token.decimals() == 12
    # Mint tokens
    uni_token.mint(t.a1, TOKEN_BALANCE_A1)
    assert uni_token.balanceOf(t.a1) == TOKEN_BALANCE_A1

def test_exchange_initial_state(t, uni_token, uniswap_multi, contract_tester, assert_tx_failed):
    start_time = t.s.head_state.timestamp
    # Mine block
    t.s.mine()
    assert uniswap_multi.invariant() == 0
    assert uniswap_multi.ethInMarket() == 0
    assert uniswap_multi.tokensInMarket() == 0
    assert uniswap_multi.totalShares() == 0
    assert u.remove_0x_head(uniswap_multi.tokenAddress()) == uni_token.address.hex()
    assert uniswap_multi.lastFeeDistribution() == start_time

def test_initialize_exchange(t, uni_token, uniswap_multi, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.approve(uniswap_multi.address, 10*TOKEN, sender=t.k1)
    # Assert starting ETH balance of test account
    assert t.s.head_state.get_balance(t.a1) == 1000000000000000000000000000000
    # Initialize exchange
    uniswap_multi.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    assert uniswap_multi.invariant() == 10*TOKEN*5*ETH
    assert uniswap_multi.ethInMarket() == 5*ETH
    assert uniswap_multi.tokensInMarket() == 10*TOKEN
    assert uni_token.balanceOf(uniswap_multi.address) == 10*TOKEN
    assert uniswap_multi.totalShares() == 1000
    # Assert final token balance of test account
    assert t.s.head_state.get_balance(uniswap_multi.address) == 5*ETH
    # Assert final ETH balance of test account
    assert t.s.head_state.get_balance(t.a1) == 1000000000000000000000000000000 - 5*ETH

def test_eth_to_tokens(t, uni_token, uniswap_multi, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.approve(uniswap_multi.address, 10*TOKEN, sender=t.k1)
    # Initialize exchange
    uniswap_multi.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    INVARIANT = 5*ETH*10*TOKEN
    # Starting Balances of buyer address
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a2) == 0
    # Buy Tokens
    uniswap_multi.ethToTokens(1, timeout, value=1*ETH, sender=t.k2)
    fee = 1*ETH/500
    assert uniswap_multi.feePool() == fee
    new_market_eth = 5*ETH + 1*ETH - fee
    assert uniswap_multi.ethInMarket() == new_market_eth
    # Contract ETH balance = eth in market + fee pool
    assert t.s.head_state.get_balance(uniswap_multi.address) == new_market_eth + fee
    new_market_tokens = int(INVARIANT/new_market_eth)
    assert uniswap_multi.tokensInMarket() == new_market_tokens
    # Contract Token balance = tokens in market
    assert uni_token.balanceOf(uniswap_multi.address) == new_market_tokens
    purchased_tokens = 10*TOKEN - new_market_tokens
    # Final Balances of buyer address
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000 - 1*ETH
    assert uni_token.balanceOf(t.a2) == purchased_tokens
    # Min tokens = 0
    assert_tx_failed(t, lambda: uniswap_multi.ethToTokens(0, timeout, value=1*ETH, sender=t.k2))
    # Purchased tokens < min tokens
    assert_tx_failed(t, lambda: uniswap_multi.ethToTokens(purchased_tokens + 1, timeout, value=1*ETH, sender=t.k2))
    # Timeout = 0
    assert_tx_failed(t, lambda: uniswap_multi.ethToTokens(1, 0, value=1*ETH, sender=t.k2))
    # Timeout < now
    assert_tx_failed(t, lambda: uniswap_multi.ethToTokens(1, timeout - 301, value=1*ETH, sender=t.k2))
    # msg.value = 0
    assert_tx_failed(t, lambda: uniswap_multi.ethToTokens(1, timeout, value=0, sender=t.k2))

def test_tokens_to_eth(t, uni_token, uniswap_multi, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.mint(t.a2, 2*TOKEN)
    uni_token.approve(uniswap_multi.address, 10*TOKEN, sender=t.k1)
    uni_token.approve(uniswap_multi.address, 2*TOKEN, sender=t.k2)
    # Initialize exchange
    uniswap_multi.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    INVARIANT = 5*ETH*10*TOKEN
    # Starting Balances of buyer address
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a2) == 2*TOKEN
    # Buy ETH
    uniswap_multi.tokenToEth(2*TOKEN, 1, timeout, sender=t.k2)
    new_market_tokens = 10*TOKEN + 2*TOKEN
    assert uniswap_multi.tokensInMarket() == new_market_tokens
    assert uni_token.balanceOf(uniswap_multi.address) == new_market_tokens
    new_market_eth = int(INVARIANT/new_market_tokens)
    assert uniswap_multi.ethInMarket() == new_market_eth + 170    # 170 wei rounding difference
    assert t.s.head_state.get_balance(uniswap_multi.address) == new_market_eth + 170  # 170 wei rounding difference
    purchased_eth = 5*ETH - new_market_eth
    fee = int(purchased_eth/500)
    assert uniswap_multi.feePool() == fee - 1     # 1 wei rounding difference
    eth_to_buyer = purchased_eth - fee
    # Final Balances of buyer address
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000 + eth_to_buyer + 1666666666666497  # LARGE rounding error of 1666666666666497
    assert uni_token.balanceOf(t.a2) == 0
    # Tokens sold = 0
    assert_tx_failed(t, lambda: uniswap_multi.tokenToEth(0, 1, timeout, sender=t.k2))
    # Tokens sold > balances[msg.sender]
    assert_tx_failed(t, lambda: uniswap_multi.tokenToEth(3*TOKEN, 1, timeout, sender=t.k2))
    # Min eth = 0
    assert_tx_failed(t, lambda: uniswap_multi.tokenToEth(2*TOKEN, 0, timeout, sender=t.k2))
    # Purchased ETH < min ETH
    assert_tx_failed(t, lambda: uniswap_multi.tokenToEth(2*TOKEN, purchased_eth + 1, timeout, sender=t.k2))
    # Timeout = 0
    assert_tx_failed(t, lambda: uniswap_multi.tokenToEth(2*TOKEN, 1, 0, sender=t.k2))
    # Timeout < now
    assert_tx_failed(t, lambda: uniswap_multi.tokenToEth(2*TOKEN, 1, timeout - 301, sender=t.k2))
