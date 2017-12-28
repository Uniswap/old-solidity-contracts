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

def test_liquidity_investment(t, uni_token, uniswap_multi, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.mint(t.a2, 30*TOKEN)
    uni_token.mint(t.a3, 2*TOKEN)
    uni_token.mint(t.a4, 10*TOKEN)
    uni_token.approve(uniswap_multi.address, 10*TOKEN, sender=t.k1)
    uni_token.approve(uniswap_multi.address, 30*TOKEN, sender=t.k2)
    uni_token.approve(uniswap_multi.address, 2*TOKEN, sender=t.k3)
    uni_token.approve(uniswap_multi.address, 10*TOKEN, sender=t.k3)
    # First provider initializes the exchange with 5 eth and 10 tokens for 1000 shares
    uniswap_multi.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    assert uniswap_multi.invariant() == 10*TOKEN*5*ETH
    assert uniswap_multi.ethInMarket() == 5*ETH
    assert uniswap_multi.tokensInMarket() == 10*TOKEN
    assert uniswap_multi.totalShares() == 1000
    assert uniswap_multi.getShares(t.a1) == 1000
    # Second provider adds 15 ETH and 30 tokens for 3000 shares
    uniswap_multi.investLiquidity(value=15*ETH, sender=t.k2)
    assert uniswap_multi.invariant() == 40*TOKEN*20*ETH
    assert uniswap_multi.ethInMarket() == 20*ETH
    assert uniswap_multi.tokensInMarket() == 40*TOKEN
    assert uniswap_multi.totalShares() == 4000
    assert uniswap_multi.getShares(t.a2) == 3000
    # Third provider adds 1 eth and 2 tokens for 200 shares
    uniswap_multi.investLiquidity(value=1*ETH, sender=t.k3)
    assert uniswap_multi.invariant() == 42*TOKEN*21*ETH
    assert uniswap_multi.ethInMarket() == 21*ETH
    assert uniswap_multi.tokensInMarket() == 42*TOKEN
    assert uniswap_multi.totalShares() == 4200
    assert uniswap_multi.getShares(t.a3) == 200
    # Not enough tokens
    assert_tx_failed(t, lambda: uniswap_multi.investLiquidity(value=20*ETH, sender=t.k4))
    # No ETH
    assert_tx_failed(t, lambda: uniswap_multi.investLiquidity(sender=t.k4))

def test_liquidity_divestment(t, uni_token, uniswap_multi, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.mint(t.a2, 30*TOKEN)
    uni_token.approve(uniswap_multi.address, 10*TOKEN, sender=t.k1)
    uni_token.approve(uniswap_multi.address, 30*TOKEN, sender=t.k2)
    uniswap_multi.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    uniswap_multi.investLiquidity(value=15*ETH, sender=t.k2)
    # Second provider divests 1000 out of his 3000 shares
    uniswap_multi.divestLiquidity(1000, sender=t.k2)
    assert uniswap_multi.invariant() == 30*TOKEN*15*ETH
    assert uniswap_multi.ethInMarket() == 15*ETH
    assert uniswap_multi.tokensInMarket() == 30*TOKEN
    assert uniswap_multi.getShares(t.a1) == 1000
    assert uniswap_multi.getShares(t.a2) == 2000
    assert uniswap_multi.totalShares() == 3000
    # First provider divests all 1000 of his shares
    uniswap_multi.divestLiquidity(1000, sender=t.k1)
    assert uniswap_multi.invariant() == 20*TOKEN*10*ETH
    assert uniswap_multi.ethInMarket() == 10*ETH
    assert uniswap_multi.tokensInMarket() == 20*TOKEN
    assert uniswap_multi.getShares(t.a1) == 0
    assert uniswap_multi.getShares(t.a2) == 2000
    assert uniswap_multi.totalShares() == 2000
    # Second provider divests all 2000 of his remaining shares
    uniswap_multi.divestLiquidity(2000, sender=t.k2)
    assert uniswap_multi.invariant() == 0
    assert uniswap_multi.getShares(t.a1) == 0
    assert uniswap_multi.getShares(t.a2) == 0
    assert uniswap_multi.totalShares() == 0
