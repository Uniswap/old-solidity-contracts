def test_initialize_exchange(t, uni_token, uni_token_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*10**18)
    uni_token.approve(uni_token_exchange.address, 10*10**18, sender=t.k1)
    # Starting balances of PROVIDER (t.a1)
    assert t.s.head_state.get_balance(t.a1) == 10**30
    assert uni_token.balanceOf(t.a1) == 10*10**18
    # PROVIDER initializes exchange
    uni_token_exchange.initializeExchange(10*10**18, value=5*10**18, sender=t.k1)
    # Updated balances of UNI exchange
    assert uni_token_exchange.invariant() == 10*10**18*5*10**18
    assert uni_token_exchange.ethPool() == 5*10**18
    assert uni_token_exchange.tokenPool() == 10*10**18
    assert uni_token.balanceOf(uni_token_exchange.address) == 10*10**18
    assert uni_token_exchange.totalShares() == 1000
    assert t.s.head_state.get_balance(uni_token_exchange.address) == 5*10**18
    # Final balances of PROVIDER
    assert t.s.head_state.get_balance(t.a1) == 10**30 - 5*10**18
    assert uni_token.balanceOf(t.a1) == 0

def test_liquidity_investment_divestment(t, uni_token, uni_token_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*10**18)
    uni_token.mint(t.a2, 30*10**18)
    uni_token.mint(t.a3, 2*10**18)
    uni_token.mint(t.a4, 10*10**18)
    uni_token.approve(uni_token_exchange.address, 10*10**18, sender=t.k1)
    uni_token.approve(uni_token_exchange.address, 30*10**18, sender=t.k2)
    uni_token.approve(uni_token_exchange.address, 2*10**18, sender=t.k3)
    uni_token.approve(uni_token_exchange.address, 10*10**18, sender=t.k3)
    # First liquidity provider initializes the exchange with 5 ETH and 10 TOKENS for 1000 shares
    uni_token_exchange.initializeExchange(10*10**18, value=5*10**18, sender=t.k1)
    assert uni_token_exchange.invariant() == 10*10**18*5*10**18
    assert uni_token_exchange.ethPool() == 5*10**18
    assert uni_token_exchange.tokenPool() == 10*10**18
    assert uni_token_exchange.totalShares() == 1000
    assert uni_token_exchange.getShares(t.a1) == 1000
    # Second liquidity provider invests 15 ETH and 30 TOKENS for 3000 shares
    uni_token_exchange.investLiquidity(1, value=15*10**18, sender=t.k2)
    assert uni_token_exchange.invariant() == 40*10**18*20*10**18
    assert uni_token_exchange.ethPool() == 20*10**18
    assert uni_token_exchange.tokenPool() == 40*10**18
    assert uni_token_exchange.totalShares() == 4000
    assert uni_token_exchange.getShares(t.a2) == 3000
    # Not enough tokens
    assert_tx_failed(t, lambda: uni_token_exchange.investLiquidity(value=20*10**18, sender=t.k4))
    # No ETH sent
    assert_tx_failed(t, lambda: uni_token_exchange.investLiquidity(sender=t.k4))
    # Second liquidity provider divests 1000 out of his 3000 shares
    uni_token_exchange.divestLiquidity(1000, 1, 1, sender=t.k2)
    assert uni_token_exchange.invariant() == 30*10**18*15*10**18
    assert uni_token_exchange.ethPool() == 15*10**18
    assert uni_token_exchange.tokenPool() == 30*10**18
    assert uni_token_exchange.getShares(t.a1) == 1000
    assert uni_token_exchange.getShares(t.a2) == 2000
    assert uni_token_exchange.totalShares() == 3000
    # First provider divests all 1000 of his shares
    uni_token_exchange.divestLiquidity(1000, 1, 1, sender=t.k1)
    assert uni_token_exchange.invariant() == 20*10**18*10*10**18
    assert uni_token_exchange.ethPool() == 10*10**18
    assert uni_token_exchange.tokenPool() == 20*10**18
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

#  NEEDS WORK
# def test_fee_divest_payout(t, uni_token, uni_token_exchange, contract_tester, assert_tx_failed):
#     t.s.mine()
#     uni_token.mint(t.a1, 10*10**18)
#     uni_token.approve(uni_token_exchange.address, 10*10**18, sender=t.k1)
#     # Starting balances of PROVIDER
#     assert t.s.head_state.get_balance(t.a1) == 10**30
#     assert uni_token.balanceOf(t.a1) == 10*10**18
#     # PROVIDER initializes exchange
#     uni_token_exchange.initializeExchange(10*10**18, value=5*10**18, sender=t.k1)
#     timeout = t.s.head_state.timestamp + 300
#     # Starting balances of PROVIDER
#     assert t.s.head_state.get_balance(t.a1) == 10**30 - 5*10**18
#     assert uni_token.balanceOf(t.a1) == 0
#     # BUYER converts ETH to UNI
#     uni_token_exchange.ethToTokenSwap(1, timeout, value=1*10**18, sender=t.k2)
#     fee = 2000000000000000                                                    # fee = 1*10**18/500
#     new_eth_pool = 6*10**18                                                   # new_eth_pool = 6*10**18
#     # temp_eth_pool = 5998000000000000000
#     # invariant = (5*10**18) * (10*10**18) = 50000000000000000000000000000000000000
#     new_token_pool = 8336112037345781927                                      # new_token_pool = int(INVARIANT/(temp_eth_pool))
#     purchased_tokens =  1663887962654218073                                   # purchased_tokens = 10*10**18 - new_token_pool
#     # Initial state of fee pool and market eth
#     assert uni_token_exchange.ethPool() == new_eth_pool
#     assert uni_token_exchange.tokenPool() == new_token_pool
#     # PROVIDER divests liquidity
#     uni_token_exchange.divestLiquidity(1000, 1, 1, sender=t.k1)
#     assert uni_token_exchange.ethPool() == 0
#     assert uni_token_exchange.tokenPool() == 0
#     # assert t.s.head_state.get_balance(t.a1) == 10**30 + 1*10**18
#     # assert uni_token.balanceOf(t.a1) == 8336112037345781927
