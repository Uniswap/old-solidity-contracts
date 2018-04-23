def test_token_to_eth_swap(t, uni_token, uni_token_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*10**18)
    uni_token.mint(t.a2, 2*10**18)
    uni_token.approve(uni_token_exchange.address, 10*10**18, sender=t.k1)
    uni_token.approve(uni_token_exchange.address, 2*10**18, sender=t.k2)
    # PROVIDER initializes exchange
    uni_token_exchange.initializeExchange(10*10**18, value=5*10**18, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    # Starting balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 10**30
    assert uni_token.balanceOf(t.a2) == 2*10**18
    # BUYER converts UNI to ETH
    uni_token_exchange.tokenToEthSwap(2*10**18, 1, timeout, sender=t.k2)
    # Updated balances of UNI exchange
    fee = 4000000000000000                        # fee = 2*10**18/500
    new_token_pool = 12*10**18                # new_token_pool = 10*10**18 + 2*10**18
    new_eth_pool = 4168056018672890963          # new_eth_pool = (5*10**18*10*10**18)/(new_token_pool - fee)
    purchased_eth = 831943981327109037           # purchased_eth = 5*10**18 - new_eth_pool
    new_invariant = 50016672224074691556000000000000000000
    assert uni_token_exchange.tokenPool() == new_token_pool
    assert uni_token.balanceOf(uni_token_exchange.address) == new_token_pool
    assert uni_token_exchange.ethPool() == new_eth_pool
    assert t.s.head_state.get_balance(uni_token_exchange.address) == new_eth_pool
    assert uni_token_exchange.invariant() == new_invariant
    # Final balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 10**30 + purchased_eth
    assert uni_token.balanceOf(t.a2) == 0
    # Tokens sold = 0
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(0, 1, timeout, sender=t.k2))
    # Tokens sold > balances[msg.sender]
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(3*10**18, 1, timeout, sender=t.k2))
    # Min eth = 0
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(2*10**18, 0, timeout, sender=t.k2))
    # Purchased ETH < min ETH
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(2*10**18, purchased_eth + 1, timeout, sender=t.k2))
    # Timeout = 0
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(2*10**18, 1, 0, sender=t.k2))
    # Timeout < now
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(2*10**18, 1, timeout - 301, sender=t.k2))

def test_token_to_eth_payment(t, uni_token, uni_token_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*10**18)
    uni_token.mint(t.a2, 2*10**18)
    uni_token.approve(uni_token_exchange.address, 10*10**18, sender=t.k1)
    uni_token.approve(uni_token_exchange.address, 2*10**18, sender=t.k2)
    # PROVIDER initializes exchange
    uni_token_exchange.initializeExchange(10*10**18, value=5*10**18, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    # Starting balances of SENDER (t.a2) and RECIPIENT (t.a3)
    assert t.s.head_state.get_balance(t.a2) == 10**30
    assert uni_token.balanceOf(t.a2) == 2*10**18
    assert t.s.head_state.get_balance(t.a3) == 10**30
    assert uni_token.balanceOf(t.a3) == 0
    # SENDER pays UNI and RECIPIENT receives ETH
    uni_token_exchange.tokenToEthPayment(2*10**18, 1, timeout, t.a3, sender=t.k2)
    # Updated balances of UNI exchange
    fee = 4000000000000000                          # fee = 2*10**18/500
    new_token_pool = 12*10**18                    # new_token_pool = 10*10**18 + 2*10**18
    new_eth_pool = 4168056018672890963              # new_eth_pool = (5*10**18*10*10**18)/(new_token_pool - fee)
    purchased_eth =  831943981327109037             # purchased_eth = 5*10**18 - new_eth_pool
    new_invariant = 50016672224074691556000000000000000000
    assert uni_token_exchange.tokenPool() == new_token_pool
    assert uni_token.balanceOf(uni_token_exchange.address) == new_token_pool
    assert uni_token_exchange.ethPool() == new_eth_pool
    assert t.s.head_state.get_balance(uni_token_exchange.address) == new_eth_pool
    assert uni_token_exchange.invariant() == new_invariant
    # Final balances of SENDER and RECIPIENT
    assert t.s.head_state.get_balance(t.a2) == 10**30
    assert uni_token.balanceOf(t.a2) == 0
    assert t.s.head_state.get_balance(t.a3) == 10**30 + purchased_eth
    assert uni_token.balanceOf(t.a3) == 0
    # Tokens sold = 0
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(0, 1, timeout, sender=t.k2))
    # Tokens sold > balances[msg.sender]
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(3*10**18, 1, timeout, sender=t.k2))
    # Min eth = 0
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(2*10**18, 0, timeout, sender=t.k2))
    # Purchased ETH < min ETH
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(2*10**18, purchased_eth + 1, timeout, sender=t.k2))
    # Timeout = 0
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(2*10**18, 1, 0, sender=t.k2))
    # Timeout < now
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(2*10**18, 1, timeout - 301, sender=t.k2))
