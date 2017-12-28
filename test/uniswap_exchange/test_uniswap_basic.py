import pytest
from ethereum import utils as u

"""
    run test with:     python3.6 -m pytest -v
"""

ETH = 10**18
TOKEN = 10**12

@pytest.fixture
def uni_token(t, contract_tester):
    return contract_tester('Token/UniToken.sol', args=[])

@pytest.fixture
def uniswap_multi(t, contract_tester, uni_token):
    return contract_tester('Exchange/UniswapLiquidityProviders.sol', args=[uni_token.address])

def test_exchange_initial_state(t, uni_token, uniswap_multi, contract_tester, assert_tx_failed):
    start_time = t.s.head_state.timestamp
    # Mine block
    t.s.mine()
    assert uniswap_multi.FEE_RATE() == 500
    assert uniswap_multi.ethInMarket() == 0
    assert uniswap_multi.tokensInMarket() == 0
    assert uniswap_multi.invariant() == 0
    assert uniswap_multi.ethFeePool() == 0
    assert uniswap_multi.tokenFeePool() == 0
    assert u.remove_0x_head(uniswap_multi.tokenAddress()) == uni_token.address.hex()
    assert uniswap_multi.totalShares() == 0
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
    assert uniswap_multi.ethFeePool() == fee
    new_market_eth = 5*ETH + 1*ETH - fee
    assert uniswap_multi.ethInMarket() == new_market_eth
    # Contract ETH balance = eth in market + fee
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
    # Starting balances of buyer address
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a2) == 2*TOKEN
    # Buy ETH
    uniswap_multi.tokenToEth(2*TOKEN, 1, timeout, sender=t.k2)
    fee = 2*TOKEN/500;
    assert uniswap_multi.tokenFeePool() == fee
    new_market_tokens = 10*TOKEN + 2*TOKEN - fee;
    assert uniswap_multi.tokensInMarket() == new_market_tokens
    # Contract token balance = tokens in market + fee
    assert uni_token.balanceOf(uniswap_multi.address) == new_market_tokens + fee
    new_market_eth = int(INVARIANT/new_market_tokens)
    # this TX has a rounding error of 429
    rounding_error = 429
    assert uniswap_multi.ethInMarket() == new_market_eth - rounding_error
    # Contract ETH balance = ETH in market
    assert t.s.head_state.get_balance(uniswap_multi.address) == new_market_eth - rounding_error
    purchased_eth = 5*ETH - new_market_eth
    # Final Balances of buyer address = starting balance + purchased eth
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000 + purchased_eth + rounding_error
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
