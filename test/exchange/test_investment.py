import pytest
from ethereum import utils as u

"""
    run test with:     pytest -v
"""

DECIMALS = 10**18

def test_initialize_exchange(t, uni_token, uni_token_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*DECIMALS)
    uni_token.approve(uni_token_exchange.address, 10*DECIMALS, sender=t.k1)
    # Starting balances of PROVIDER (t.a1)
    assert t.s.head_state.get_balance(t.a1) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a1) == 10000000000000000000
    # PROVIDER initializes exchange
    uni_token_exchange.initializeExchange(10*DECIMALS, value=5*DECIMALS, sender=t.k1)
    # Updated balances of UNI exchange
    assert uni_token_exchange.invariant() == 10*DECIMALS*5*DECIMALS
    assert uni_token_exchange.ethPool() == 5*DECIMALS
    assert uni_token_exchange.tokenPool() == 10*DECIMALS
    assert uni_token.balanceOf(uni_token_exchange.address) == 10*DECIMALS
    assert uni_token_exchange.totalShares() == 1000
    assert t.s.head_state.get_balance(uni_token_exchange.address) == 5*DECIMALS
    # Final balances of PROVIDER
    assert t.s.head_state.get_balance(t.a1) == 1000000000000000000000000000000 - 5*DECIMALS
    assert uni_token.balanceOf(t.a1) == 0

def test_liquidity_investment_divestment(t, uni_token, uni_token_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*DECIMALS)
    uni_token.mint(t.a2, 30*DECIMALS)
    uni_token.mint(t.a3, 2*DECIMALS)
    uni_token.mint(t.a4, 10*DECIMALS)
    uni_token.approve(uni_token_exchange.address, 10*DECIMALS, sender=t.k1)
    uni_token.approve(uni_token_exchange.address, 30*DECIMALS, sender=t.k2)
    uni_token.approve(uni_token_exchange.address, 2*DECIMALS, sender=t.k3)
    uni_token.approve(uni_token_exchange.address, 10*DECIMALS, sender=t.k3)
    # First liquidity provider initializes the exchange with 5 ETH and 10 TOKENS for 1000 shares
    uni_token_exchange.initializeExchange(10*DECIMALS, value=5*DECIMALS, sender=t.k1)
    assert uni_token_exchange.invariant() == 10*DECIMALS*5*DECIMALS
    assert uni_token_exchange.ethPool() == 5*DECIMALS
    assert uni_token_exchange.tokenPool() == 10*DECIMALS
    assert uni_token_exchange.totalShares() == 1000
    assert uni_token_exchange.getShares(t.a1) == 1000
    # Second liquidity provider invests 15 ETH and 30 TOKENS for 3000 shares
    uni_token_exchange.investLiquidity(1, value=15*DECIMALS, sender=t.k2)
    assert uni_token_exchange.invariant() == 40*DECIMALS*20*DECIMALS
    assert uni_token_exchange.ethPool() == 20*DECIMALS
    assert uni_token_exchange.tokenPool() == 40*DECIMALS
    assert uni_token_exchange.totalShares() == 4000
    assert uni_token_exchange.getShares(t.a2) == 3000
    # Not enough tokens
    assert_tx_failed(t, lambda: uni_token_exchange.investLiquidity(value=20*DECIMALS, sender=t.k4))
    # No ETH sent
    assert_tx_failed(t, lambda: uni_token_exchange.investLiquidity(sender=t.k4))
    # Second liquidity provider divests 1000 out of his 3000 shares
    uni_token_exchange.divestLiquidity(1000, 1, 1, sender=t.k2)
    assert uni_token_exchange.invariant() == 30*DECIMALS*15*DECIMALS
    assert uni_token_exchange.ethPool() == 15*DECIMALS
    assert uni_token_exchange.tokenPool() == 30*DECIMALS
    assert uni_token_exchange.getShares(t.a1) == 1000
    assert uni_token_exchange.getShares(t.a2) == 2000
    assert uni_token_exchange.totalShares() == 3000
    # First provider divests all 1000 of his shares
    uni_token_exchange.divestLiquidity(1000, 1, 1, sender=t.k1)
    assert uni_token_exchange.invariant() == 20*DECIMALS*10*DECIMALS
    assert uni_token_exchange.ethPool() == 10*DECIMALS
    assert uni_token_exchange.tokenPool() == 20*DECIMALS
    assert uni_token_exchange.getShares(t.a1) == 0
    assert uni_token_exchange.getShares(t.a2) == 2000
    assert uni_token_exchange.totalShares() == 2000
    # Not enough shares
    assert_tx_failed(t, lambda: uni_token_exchange.divestLiquidity(3000, sender=t.k2))
    # Shares cannnot be zero
    assert_tx_failed(t, lambda: uni_token_exchange.divestLiquidity(0, sender=t.k2))
    # No missing parameters
    assert_tx_failed(t, lambda: uni_token_exchange.divestLiquidity(sender=t.k2))
    # Second provider divests his remaining shares
    uni_token_exchange.divestLiquidity(2000, 1, 1, sender=t.k2)
    assert uni_token_exchange.getShares(t.a1) == 0
    assert uni_token_exchange.getShares(t.a2) == 0
    assert uni_token_exchange.totalShares() == 0
    assert uni_token_exchange.invariant() == 0

def test_public_fee_payout(t, uni_token, uni_token_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*DECIMALS)
    uni_token.approve(uni_token_exchange.address, 10*DECIMALS, sender=t.k1)
    # PROVIDER initializes exchange
    uni_token_exchange.initializeExchange(10*DECIMALS, value=5*DECIMALS, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    # BUYER converts ETH to UNI
    uni_token_exchange.ethToTokenSwap(1, timeout, value=1*DECIMALS, sender=t.k2)
    INVARIANT = 5*DECIMALS*10*DECIMALS
    fee = 1*DECIMALS/500
    new_market_eth = 5*DECIMALS + 1*DECIMALS - fee
    new_market_tokens = int(INVARIANT/new_market_eth)
    purchased_tokens = 10*DECIMALS - new_market_tokens
    # Initial state of fee pool and market eth
    assert uni_token_exchange.ethFees() == fee
    assert uni_token_exchange.ethPool() == new_market_eth
    assert t.s.head_state.get_balance(uni_token_exchange.address) == new_market_eth + fee
    # Person adds fees to market
    uni_token_exchange.addFeesToMarketPublic()
    # Updated state of fee pool and market eth
    assert uni_token_exchange.ethFees() == 0
    assert uni_token_exchange.ethPool() == new_market_eth + fee
    assert t.s.head_state.get_balance(uni_token_exchange.address) == new_market_eth + fee
    # Can't add fees to market if fee pool is empty
    assert_tx_failed(t, lambda: uni_token_exchange.addFeesToMarketPublic())

def test_fee_invest_payout(t, uni_token, uni_token_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*DECIMALS)
    uni_token.approve(uni_token_exchange.address, 10*DECIMALS, sender=t.k1)
    # PROVIDER initializes exchange
    uni_token_exchange.initializeExchange(10*DECIMALS, value=5*DECIMALS, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    # BUYER converts ETH to UNI
    uni_token_exchange.ethToTokenSwap(1, timeout, value=1*DECIMALS, sender=t.k2)
    INVARIANT = 5*DECIMALS*10*DECIMALS
    fee = 1*DECIMALS/500
    new_market_eth = 5*DECIMALS + 1*DECIMALS - fee
    new_market_tokens = int(INVARIANT/new_market_eth)
    purchased_tokens = 10*DECIMALS - new_market_tokens
    # Initial state of fee pool and market eth
    assert uni_token_exchange.ethFees() == fee
    assert uni_token_exchange.ethPool() == new_market_eth
    uni_token.mint(t.a2, 30*DECIMALS)
    uni_token.approve(uni_token_exchange.address, 30*DECIMALS, sender=t.k2)
    uni_token_exchange.investLiquidity(1, value=15*DECIMALS, sender=t.k2)
    assert uni_token_exchange.ethFees() == 0
    assert uni_token_exchange.ethPool() == new_market_eth + 15*DECIMALS + fee

def test_fee_divest_payout(t, uni_token, uni_token_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*DECIMALS)
    uni_token.approve(uni_token_exchange.address, 10*DECIMALS, sender=t.k1)
    # PROVIDER initializes exchange
    uni_token_exchange.initializeExchange(10*DECIMALS, value=5*DECIMALS, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    # BUYER converts ETH to UNI
    uni_token_exchange.ethToTokenSwap(1, timeout, value=1*DECIMALS, sender=t.k2)
    INVARIANT = 5*DECIMALS*10*DECIMALS
    fee = 1*DECIMALS/500
    new_market_eth = 5*DECIMALS + 1*DECIMALS - fee
    new_market_tokens = int(INVARIANT/new_market_eth)
    purchased_tokens = 10*DECIMALS - new_market_tokens
    # Initial state of fee pool and market eth
    assert uni_token_exchange.ethFees() == fee
    assert uni_token_exchange.ethPool() == new_market_eth
    uni_token_exchange.divestLiquidity(500, 1, 1, sender=t.k1)
    assert uni_token_exchange.ethFees() == 0
    assert uni_token_exchange.ethPool() == (new_market_eth + fee)/2
