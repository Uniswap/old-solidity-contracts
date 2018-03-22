import pytest
from ethereum import utils as u

"""
    run test with:     pytest -v
"""

DECIMALS = 10**18

def test_eth_to_token_swap(t, uni_token, uni_token_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*DECIMALS)
    uni_token.approve(uni_token_exchange.address, 10*DECIMALS, sender=t.k1)
    # PROVIDER initializes exchange
    uni_token_exchange.initializeExchange(10*DECIMALS, value=5*DECIMALS, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    # Starting balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a2) == 0
    # BUYER converts ETH to UNI
    uni_token_exchange.ethToTokenSwap(1, timeout, value=1*DECIMALS, sender=t.k2)
    # Updated balances of UNI exchange
    fee = 2000000000000000                                # fee = 1*DECIMALS/500
    new_market_eth = 5998000000000000000                  # new_market_eth = 5*DECIMALS + 1*DECIMALS - fee
    new_market_tokens = 8336112037345781927               # new_market_tokens = (5*DECIMALS*10*DECIMALS)/new_market_eth
    purchased_tokens = 1663887962654218073                # purchased_tokens = 10*DECIMALS - new_market_tokens
    assert uni_token_exchange.ethFees() == fee
    assert uni_token_exchange.ethPool() == new_market_eth
    assert t.s.head_state.get_balance(uni_token_exchange.address) == new_market_eth + fee
    assert uni_token_exchange.tokenPool() == new_market_tokens
    assert uni_token.balanceOf(uni_token_exchange.address) == new_market_tokens
    # Final balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000 - 1*DECIMALS
    assert uni_token.balanceOf(t.a2) == purchased_tokens
    # Min tokens = 0
    assert_tx_failed(t, lambda: uni_token_exchange.ethToTokenSwap(0, timeout, value=1*DECIMALS, sender=t.k2))
    # Purchased tokens < min tokens
    assert_tx_failed(t, lambda: uni_token_exchange.ethToTokenSwap(purchased_tokens + 1, timeout, value=1*DECIMALS, sender=t.k2))
    # Timeout = 0
    assert_tx_failed(t, lambda: uni_token_exchange.ethToTokenSwap(1, 0, value=1*DECIMALS, sender=t.k2))
    # Timeout < now
    assert_tx_failed(t, lambda: uni_token_exchange.ethToTokenSwap(1, timeout - 301, value=1*DECIMALS, sender=t.k2))
    # msg.value = 0
    assert_tx_failed(t, lambda: uni_token_exchange.ethToTokenSwap(1, timeout, value=0, sender=t.k2))

def test_fallback_eth_to_token_swap(t, uni_token, uni_token_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*DECIMALS)
    uni_token.approve(uni_token_exchange.address, 10*DECIMALS, sender=t.k1)
    # PROVIDER initializes exchange
    uni_token_exchange.initializeExchange(10*DECIMALS, value=5*DECIMALS, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    # Starting balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a2) == 0
    # BUYER converts ETH to UNI
    t.s.tx(to=uni_token_exchange.address, startgas=90000, value=1*DECIMALS, sender=t.k2)
    # Updated balances of UNI exchange
    fee = 2000000000000000                                # fee = 1*DECIMALS/500
    new_market_eth = 5998000000000000000                  # new_market_eth = 5*DECIMALS + 1*DECIMALS - fee
    new_market_tokens = 8336112037345781927               # new_market_tokens = (5*DECIMALS*10*DECIMALS)/new_market_eth
    purchased_tokens = 1663887962654218073                # purchased_tokens = 10*DECIMALS - new_market_tokens
    assert uni_token_exchange.ethFees() == fee
    assert uni_token_exchange.ethPool() == new_market_eth
    assert t.s.head_state.get_balance(uni_token_exchange.address) == new_market_eth + fee
    assert uni_token_exchange.tokenPool() == new_market_tokens
    assert uni_token.balanceOf(uni_token_exchange.address) == new_market_tokens
    # Final balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000 - 1*DECIMALS
    assert uni_token.balanceOf(t.a2) == purchased_tokens
    # msg.value = 0
    assert_tx_failed(t, lambda: t.s.tx(to=uni_token_exchange.address, startgas=90000, sender=t.k2))
    # not enough gas
    assert_tx_failed(t, lambda: t.s.tx(to=uni_token_exchange.address, startgas=21000, value=1*DECIMALS, sender=t.k2))

def test_eth_to_token_payment(t, uni_token, uni_token_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*DECIMALS)
    uni_token.approve(uni_token_exchange.address, 10*DECIMALS, sender=t.k1)
    # PROVIDER (t.a1) initializes exchange
    uni_token_exchange.initializeExchange(10*DECIMALS, value=5*DECIMALS, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    # Starting balances of SENDER (t.a2) and RECIPIENT (t.a3)
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a2) == 0
    assert t.s.head_state.get_balance(t.a3) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a3) == 0
    # SENDER pays ETH and RECIPIENT receives UNI
    uni_token_exchange.ethToTokenPayment(1, timeout, t.a3, value=1*DECIMALS, sender=t.k2)
    # Updated balances of UNI exchange
    fee = 2000000000000000                                # fee = 1*DECIMALS/500
    new_market_eth = 5998000000000000000                  # new_market_eth = 5*DECIMALS + 1*DECIMALS - fee
    new_market_tokens = 8336112037345781927               # new_market_tokens = (5*DECIMALS*10*DECIMALS)/new_market_eth
    purchased_tokens = 1663887962654218073                # purchased_tokens = 10*DECIMALS - new_market_tokens
    assert uni_token_exchange.ethFees() == fee
    assert uni_token_exchange.ethPool() == new_market_eth
    assert t.s.head_state.get_balance(uni_token_exchange.address) == new_market_eth + fee
    assert uni_token_exchange.tokenPool() == new_market_tokens
    assert uni_token.balanceOf(uni_token_exchange.address) == new_market_tokens
    # Final balances of BUYER and RECIPIENT
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000 - 1*DECIMALS
    assert uni_token.balanceOf(t.a2) == 0
    assert t.s.head_state.get_balance(t.a3) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a3) == purchased_tokens
    # Min tokens = 0
    assert_tx_failed(t, lambda: uni_token_exchange.ethToTokenPayment(0, timeout, t.a3, value=1*DECIMALS, sender=t.k2))
    # Purchased tokens < min tokens
    assert_tx_failed(t, lambda: uni_token_exchange.ethToTokenPayment(purchased_tokens + 1, timeout, t.a3, value=1*DECIMALS, sender=t.k2))
    # Timeout = 0
    assert_tx_failed(t, lambda: uni_token_exchange.ethToTokenPayment(1, 0, t.a3, value=1*DECIMALS, sender=t.k2))
    # Timeout < now
    assert_tx_failed(t, lambda: uni_token_exchange.ethToTokenPayment(1, timeout - 301, t.a3, value=1*DECIMALS, sender=t.k2))
    # msg.value = 0
    assert_tx_failed(t, lambda: uni_token_exchange.ethToTokenPayment(1, timeout, t.a3, value=0, sender=t.k2))
