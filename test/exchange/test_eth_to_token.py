def test_eth_to_token_swap(t, uni_token, uni_token_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*10**18)
    uni_token.approve(uni_token_exchange.address, 10*10**18, sender=t.k1)
    # PROVIDER initializes exchange
    uni_token_exchange.initializeExchange(10*10**18, value=5*10**18, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    # Starting balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 10**30
    assert uni_token.balanceOf(t.a2) == 0
    # BUYER converts ETH to UNI
    uni_token_exchange.ethToTokenSwap(1, timeout, value=1*10**18, sender=t.k2)
    # Updated balances of UNI exchange
    fee = 2000000000000000                                      # fee = 1*10**18/500
    new_eth_pool = 6*10**18                                     # new_eth_pool = 5*10**18 + 1*10**18 - fee
    new_token_pool = 8336112037345781927                        # new_token_pool = (5*10**18*10*10**18)/(new_eth_pool - fee)
    purchased_tokens = 1663887962654218073                      # purchased_tokens = 10*10**18 - new_token_pool
    new_invariant = 50016672224074691562000000000000000000
    assert uni_token_exchange.ethPool() == new_eth_pool
    assert t.s.head_state.get_balance(uni_token_exchange.address) == new_eth_pool
    assert uni_token_exchange.tokenPool() == new_token_pool
    assert uni_token.balanceOf(uni_token_exchange.address) == new_token_pool
    assert uni_token_exchange.invariant() == new_invariant
    # Final balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 10**30 - 1*10**18
    assert uni_token.balanceOf(t.a2) == purchased_tokens
    # Min tokens = 0
    assert_tx_failed(t, lambda: uni_token_exchange.ethToTokenSwap(0, timeout, value=1*10**18, sender=t.k2))
    # Purchased tokens < min tokens
    assert_tx_failed(t, lambda: uni_token_exchange.ethToTokenSwap(purchased_tokens + 1, timeout, value=1*10**18, sender=t.k2))
    # Timeout = 0
    assert_tx_failed(t, lambda: uni_token_exchange.ethToTokenSwap(1, 0, value=1*10**18, sender=t.k2))
    # Timeout < now
    assert_tx_failed(t, lambda: uni_token_exchange.ethToTokenSwap(1, timeout - 301, value=1*10**18, sender=t.k2))
    # msg.value = 0
    assert_tx_failed(t, lambda: uni_token_exchange.ethToTokenSwap(1, timeout, value=0, sender=t.k2))

def test_fallback_eth_to_token_swap(t, uni_token, uni_token_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*10**18)
    uni_token.approve(uni_token_exchange.address, 10*10**18, sender=t.k1)
    # PROVIDER initializes exchange
    uni_token_exchange.initializeExchange(10*10**18, value=5*10**18, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    # Starting balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 10**30
    assert uni_token.balanceOf(t.a2) == 0
    # BUYER converts ETH to UNI
    t.s.tx(to=uni_token_exchange.address, startgas=90000, value=1*10**18, sender=t.k2)
    # Updated balances of UNI exchange
    fee = 2000000000000000                                          # fee = 1*10**18/500
    new_eth_pool = 6*10**18                                         # new_eth_pool = 5*10**18 + 1*10**18 - fee
    new_token_pool = 8336112037345781927                            # new_token_pool = (5*10**18*10*10**18)/(new_eth_pool - fee)
    purchased_tokens = 1663887962654218073                          # purchased_tokens = 10*10**18 - new_token_pool
    new_invariant = 50016672224074691562000000000000000000
    assert uni_token_exchange.ethPool() == new_eth_pool
    assert t.s.head_state.get_balance(uni_token_exchange.address) == new_eth_pool
    assert uni_token_exchange.tokenPool() == new_token_pool
    assert uni_token.balanceOf(uni_token_exchange.address) == new_token_pool
    assert uni_token_exchange.invariant() == new_invariant
    # Final balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 10**30 - 1*10**18
    assert uni_token.balanceOf(t.a2) == purchased_tokens
    # msg.value = 0
    assert_tx_failed(t, lambda: t.s.tx(to=uni_token_exchange.address, startgas=90000, sender=t.k2))
    # not enough gas
    assert_tx_failed(t, lambda: t.s.tx(to=uni_token_exchange.address, startgas=21000, value=1*10**18, sender=t.k2))

def test_eth_to_token_payment(t, uni_token, uni_token_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*10**18)
    uni_token.approve(uni_token_exchange.address, 10*10**18, sender=t.k1)
    # PROVIDER (t.a1) initializes exchange
    uni_token_exchange.initializeExchange(10*10**18, value=5*10**18, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    # Starting balances of SENDER (t.a2) and RECIPIENT (t.a3)
    assert t.s.head_state.get_balance(t.a2) == 10**30
    assert uni_token.balanceOf(t.a2) == 0
    assert t.s.head_state.get_balance(t.a3) == 10**30
    assert uni_token.balanceOf(t.a3) == 0
    # SENDER pays ETH and RECIPIENT receives UNI
    uni_token_exchange.ethToTokenPayment(1, timeout, t.a3, value=1*10**18, sender=t.k2)
    # Updated balances of UNI exchange
    fee = 2000000000000000                                          # fee = 1*10**18/500
    new_eth_pool = 6*10**18                                         # new_eth_pool = 5*10**18 + 1*10**18
    new_token_pool = 8336112037345781927                            # new_token_pool = (5*10**18*10*10**18)/(new_eth_pool - fee)
    purchased_tokens = 1663887962654218073                          # purchased_tokens = 10*10**18 - new_token_pool
    new_invariant = 50016672224074691562000000000000000000
    assert uni_token_exchange.ethPool() == new_eth_pool
    assert t.s.head_state.get_balance(uni_token_exchange.address) == new_eth_pool
    assert uni_token_exchange.tokenPool() == new_token_pool
    assert uni_token.balanceOf(uni_token_exchange.address) == new_token_pool
    assert uni_token_exchange.invariant() == new_invariant
    # Final balances of BUYER and RECIPIENT
    assert t.s.head_state.get_balance(t.a2) == 10**30 - 1*10**18
    assert uni_token.balanceOf(t.a2) == 0
    assert t.s.head_state.get_balance(t.a3) == 10**30
    assert uni_token.balanceOf(t.a3) == purchased_tokens
    # Min tokens = 0
    assert_tx_failed(t, lambda: uni_token_exchange.ethToTokenPayment(0, timeout, t.a3, value=1*10**18, sender=t.k2))
    # Purchased tokens < min tokens
    assert_tx_failed(t, lambda: uni_token_exchange.ethToTokenPayment(purchased_tokens + 1, timeout, t.a3, value=1*10**18, sender=t.k2))
    # Timeout = 0
    assert_tx_failed(t, lambda: uni_token_exchange.ethToTokenPayment(1, 0, t.a3, value=1*10**18, sender=t.k2))
    # Timeout < now
    assert_tx_failed(t, lambda: uni_token_exchange.ethToTokenPayment(1, timeout - 301, t.a3, value=1*10**18, sender=t.k2))
    # msg.value = 0
    assert_tx_failed(t, lambda: uni_token_exchange.ethToTokenPayment(1, timeout, t.a3, value=0, sender=t.k2))
