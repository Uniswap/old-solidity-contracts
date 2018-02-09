import pytest
from ethereum import utils as u

"""
    run test with:     pytest -v
"""

ETH = 10**18
TOKEN = 10**18

@pytest.fixture
def uni_token(t, contract_tester):
    return contract_tester('Token/UniToken.sol', args=[])

@pytest.fixture
def uniswap_exchange(t, contract_tester, uni_token):
    return contract_tester('Exchange/UniswapExchange.sol', args=[uni_token.address])

def test_liquidity_investment(t, uni_token, uniswap_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.mint(t.a2, 30*TOKEN)
    uni_token.mint(t.a3, 2*TOKEN)
    uni_token.mint(t.a4, 10*TOKEN)
    uni_token.approve(uniswap_exchange.address, 10*TOKEN, sender=t.k1)
    uni_token.approve(uniswap_exchange.address, 30*TOKEN, sender=t.k2)
    uni_token.approve(uniswap_exchange.address, 2*TOKEN, sender=t.k3)
    uni_token.approve(uniswap_exchange.address, 10*TOKEN, sender=t.k3)
    # First provider initializes the exchange with 5 eth and 10 tokens for 1000 shares
    uniswap_exchange.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    assert uniswap_exchange.invariant() == 10*TOKEN*5*ETH
    assert uniswap_exchange.ethInMarket() == 5*ETH
    assert uniswap_exchange.tokensInMarket() == 10*TOKEN
    assert uniswap_exchange.totalShares() == 1000
    assert uniswap_exchange.getShares(t.a1) == 1000
    # Second provider adds 15 ETH and 30 tokens for 3000 shares
    uniswap_exchange.investLiquidity(1, value=15*ETH, sender=t.k2)
    assert uniswap_exchange.invariant() == 40*TOKEN*20*ETH
    assert uniswap_exchange.ethInMarket() == 20*ETH
    assert uniswap_exchange.tokensInMarket() == 40*TOKEN
    assert uniswap_exchange.totalShares() == 4000
    assert uniswap_exchange.getShares(t.a2) == 3000
    # Third provider adds 1 eth and 2 tokens for 200 shares
    uniswap_exchange.investLiquidity(1, value=1*ETH, sender=t.k3)
    assert uniswap_exchange.invariant() == 42*TOKEN*21*ETH
    assert uniswap_exchange.ethInMarket() == 21*ETH
    assert uniswap_exchange.tokensInMarket() == 42*TOKEN
    assert uniswap_exchange.totalShares() == 4200
    assert uniswap_exchange.getShares(t.a3) == 200
    # Not enough tokens
    assert_tx_failed(t, lambda: uniswap_exchange.investLiquidity(value=20*ETH, sender=t.k4))
    # No ETH
    assert_tx_failed(t, lambda: uniswap_exchange.investLiquidity(sender=t.k4))

def test_liquidity_divestment(t, uni_token, uniswap_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.mint(t.a2, 30*TOKEN)
    uni_token.approve(uniswap_exchange.address, 10*TOKEN, sender=t.k1)
    uni_token.approve(uniswap_exchange.address, 30*TOKEN, sender=t.k2)
    uniswap_exchange.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    uniswap_exchange.investLiquidity(1, value=15*ETH, sender=t.k2)
    # Second provider divests 1000 out of his 3000 shares
    uniswap_exchange.divestLiquidity(1000, 1, 1, sender=t.k2)
    assert uniswap_exchange.invariant() == 30*TOKEN*15*ETH
    assert uniswap_exchange.ethInMarket() == 15*ETH
    assert uniswap_exchange.tokensInMarket() == 30*TOKEN
    assert uniswap_exchange.getShares(t.a1) == 1000
    assert uniswap_exchange.getShares(t.a2) == 2000
    assert uniswap_exchange.totalShares() == 3000
    # First provider divests all 1000 of his shares
    uniswap_exchange.divestLiquidity(1000, 1, 1, sender=t.k1)
    assert uniswap_exchange.invariant() == 20*TOKEN*10*ETH
    assert uniswap_exchange.ethInMarket() == 10*ETH
    assert uniswap_exchange.tokensInMarket() == 20*TOKEN
    assert uniswap_exchange.getShares(t.a1) == 0
    assert uniswap_exchange.getShares(t.a2) == 2000
    assert uniswap_exchange.totalShares() == 2000
    # Not enough shares
    assert_tx_failed(t, lambda: uniswap_exchange.divestLiquidity(3000, sender=t.k2))
    # Shares cannnot be zero
    assert_tx_failed(t, lambda: uniswap_exchange.divestLiquidity(0, sender=t.k2))
    # No missing parameters
    assert_tx_failed(t, lambda: uniswap_exchange.divestLiquidity(sender=t.k2))
    # Second provider divests all 2000 of his remaining shares
    uniswap_exchange.divestLiquidity(2000, 1, 1, sender=t.k2)
    assert uniswap_exchange.getShares(t.a1) == 0
    assert uniswap_exchange.getShares(t.a2) == 0
    assert uniswap_exchange.totalShares() == 0
    assert uniswap_exchange.invariant() == 0


def test_public_fee_payout(t, uni_token, uniswap_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.approve(uniswap_exchange.address, 10*TOKEN, sender=t.k1)
    # PROVIDER initializes exchange
    uniswap_exchange.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    # BUYER converts ETH to UNI
    uniswap_exchange.ethToTokenSwap(1, timeout, value=1*ETH, sender=t.k2)
    INVARIANT = 5*ETH*10*TOKEN
    fee = 1*ETH/500
    new_market_eth = 5*ETH + 1*ETH - fee
    new_market_tokens = int(INVARIANT/new_market_eth)
    purchased_tokens = 10*TOKEN - new_market_tokens
    # Initial state of fee pool and market eth
    assert uniswap_exchange.ethFees() == fee
    assert uniswap_exchange.ethInMarket() == new_market_eth
    assert t.s.head_state.get_balance(uniswap_exchange.address) == new_market_eth + fee
    # Person adds fees to market
    uniswap_exchange.addFeesToMarketPublic()
    # Updated state of fee pool and market eth
    assert uniswap_exchange.ethFees() == 0
    assert uniswap_exchange.ethInMarket() == new_market_eth + fee
    assert t.s.head_state.get_balance(uniswap_exchange.address) == new_market_eth + fee
    # Can't add fees to market if fee pool is empty
    assert_tx_failed(t, lambda: uniswap_exchange.addFeesToMarketPublic())

def test_fee_invest_payout(t, uni_token, uniswap_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.approve(uniswap_exchange.address, 10*TOKEN, sender=t.k1)
    # PROVIDER initializes exchange
    uniswap_exchange.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    # BUYER converts ETH to UNI
    uniswap_exchange.ethToTokenSwap(1, timeout, value=1*ETH, sender=t.k2)
    INVARIANT = 5*ETH*10*TOKEN
    fee = 1*ETH/500
    new_market_eth = 5*ETH + 1*ETH - fee
    new_market_tokens = int(INVARIANT/new_market_eth)
    purchased_tokens = 10*TOKEN - new_market_tokens
    # Initial state of fee pool and market eth
    assert uniswap_exchange.ethFees() == fee
    assert uniswap_exchange.ethInMarket() == new_market_eth
    uni_token.mint(t.a2, 30*TOKEN)
    uni_token.approve(uniswap_exchange.address, 30*TOKEN, sender=t.k2)
    uniswap_exchange.investLiquidity(1, value=15*ETH, sender=t.k2)
    assert uniswap_exchange.ethFees() == 0
    assert uniswap_exchange.ethInMarket() == new_market_eth + 15*ETH + fee

def test_fee_divest_payout(t, uni_token, uniswap_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.approve(uniswap_exchange.address, 10*TOKEN, sender=t.k1)
    # PROVIDER initializes exchange
    uniswap_exchange.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    # BUYER converts ETH to UNI
    uniswap_exchange.ethToTokenSwap(1, timeout, value=1*ETH, sender=t.k2)
    INVARIANT = 5*ETH*10*TOKEN
    fee = 1*ETH/500
    new_market_eth = 5*ETH + 1*ETH - fee
    new_market_tokens = int(INVARIANT/new_market_eth)
    purchased_tokens = 10*TOKEN - new_market_tokens
    # Initial state of fee pool and market eth
    assert uniswap_exchange.ethFees() == fee
    assert uniswap_exchange.ethInMarket() == new_market_eth
    uniswap_exchange.divestLiquidity(500, 1, 1, sender=t.k1)
    assert uniswap_exchange.ethFees() == 0
    assert uniswap_exchange.ethInMarket() == (new_market_eth + fee)/2
