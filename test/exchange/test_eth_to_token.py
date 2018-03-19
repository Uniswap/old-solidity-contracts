import pytest
from ethereum import utils as u

"""
    run test with:     pytest -v
"""

ETH = 10**18
TOKEN = 10**18

def test_eth_to_token_swap(t, uni_token, uniswap_exchange, contract_tester, assert_tx_failed):
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
    uniswap_exchange.ethToTokenSwap(1, timeout, value=1*ETH, sender=t.k2)
    # Updated balances of UNI exchange
    fee = 2000000000000000                                # fee = 1*ETH/500
    new_market_eth = 5998000000000000000                  # new_market_eth = 5*ETH + 1*ETH - fee
    new_market_tokens = 8336112037345781927               # new_market_tokens = (5*ETH*10*TOKEN)/new_market_eth
    purchased_tokens = 1663887962654218073                # purchased_tokens = 10*TOKEN - new_market_tokens
    assert uniswap_exchange.ethFees() == fee
    assert uniswap_exchange.ethPool() == new_market_eth
    assert t.s.head_state.get_balance(uniswap_exchange.address) == new_market_eth + fee
    assert uniswap_exchange.tokenPool() == new_market_tokens
    assert uni_token.balanceOf(uniswap_exchange.address) == new_market_tokens
    # Final balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000 - 1*ETH
    assert uni_token.balanceOf(t.a2) == purchased_tokens
    # Min tokens = 0
    assert_tx_failed(t, lambda: uniswap_exchange.ethToTokenSwap(0, timeout, value=1*ETH, sender=t.k2))
    # Purchased tokens < min tokens
    assert_tx_failed(t, lambda: uniswap_exchange.ethToTokenSwap(purchased_tokens + 1, timeout, value=1*ETH, sender=t.k2))
    # Timeout = 0
    assert_tx_failed(t, lambda: uniswap_exchange.ethToTokenSwap(1, 0, value=1*ETH, sender=t.k2))
    # Timeout < now
    assert_tx_failed(t, lambda: uniswap_exchange.ethToTokenSwap(1, timeout - 301, value=1*ETH, sender=t.k2))
    # msg.value = 0
    assert_tx_failed(t, lambda: uniswap_exchange.ethToTokenSwap(1, timeout, value=0, sender=t.k2))

def test_fallback_eth_to_token_swap(t, uni_token, uniswap_exchange, contract_tester, assert_tx_failed):
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
    t.s.tx(to=uniswap_exchange.address, startgas=90000, value=1*ETH, sender=t.k2)
    # Updated balances of UNI exchange
    fee = 2000000000000000                                # fee = 1*ETH/500
    new_market_eth = 5998000000000000000                  # new_market_eth = 5*ETH + 1*ETH - fee
    new_market_tokens = 8336112037345781927               # new_market_tokens = (5*ETH*10*TOKEN)/new_market_eth
    purchased_tokens = 1663887962654218073                # purchased_tokens = 10*TOKEN - new_market_tokens
    assert uniswap_exchange.ethFees() == fee
    assert uniswap_exchange.ethPool() == new_market_eth
    assert t.s.head_state.get_balance(uniswap_exchange.address) == new_market_eth + fee
    assert uniswap_exchange.tokenPool() == new_market_tokens
    assert uni_token.balanceOf(uniswap_exchange.address) == new_market_tokens
    # Final balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000 - 1*ETH
    assert uni_token.balanceOf(t.a2) == purchased_tokens
    # msg.value = 0
    assert_tx_failed(t, lambda: t.s.tx(to=uniswap_exchange.address, startgas=90000, sender=t.k2))
    # not enough gas
    assert_tx_failed(t, lambda: t.s.tx(to=uniswap_exchange.address, startgas=21000, value=1*ETH, sender=t.k2))

def test_eth_to_token_payment(t, uni_token, uniswap_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.approve(uniswap_exchange.address, 10*TOKEN, sender=t.k1)
    # PROVIDER (t.a1) initializes exchange
    uniswap_exchange.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    # Starting balances of SENDER (t.a2) and RECIPIENT (t.a3)
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a2) == 0
    assert t.s.head_state.get_balance(t.a3) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a3) == 0
    # SENDER pays ETH and RECIPIENT receives UNI
    uniswap_exchange.ethToTokenPayment(1, timeout, t.a3, value=1*ETH, sender=t.k2)
    # Updated balances of UNI exchange
    fee = 2000000000000000                                # fee = 1*ETH/500
    new_market_eth = 5998000000000000000                  # new_market_eth = 5*ETH + 1*ETH - fee
    new_market_tokens = 8336112037345781927               # new_market_tokens = (5*ETH*10*TOKEN)/new_market_eth
    purchased_tokens = 1663887962654218073                # purchased_tokens = 10*TOKEN - new_market_tokens
    assert uniswap_exchange.ethFees() == fee
    assert uniswap_exchange.ethPool() == new_market_eth
    assert t.s.head_state.get_balance(uniswap_exchange.address) == new_market_eth + fee
    assert uniswap_exchange.tokenPool() == new_market_tokens
    assert uni_token.balanceOf(uniswap_exchange.address) == new_market_tokens
    # Final balances of BUYER and RECIPIENT
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000 - 1*ETH
    assert uni_token.balanceOf(t.a2) == 0
    assert t.s.head_state.get_balance(t.a3) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a3) == purchased_tokens
    # Min tokens = 0
    assert_tx_failed(t, lambda: uniswap_exchange.ethToTokenPayment(0, timeout, t.a3, value=1*ETH, sender=t.k2))
    # Purchased tokens < min tokens
    assert_tx_failed(t, lambda: uniswap_exchange.ethToTokenPayment(purchased_tokens + 1, timeout, t.a3, value=1*ETH, sender=t.k2))
    # Timeout = 0
    assert_tx_failed(t, lambda: uniswap_exchange.ethToTokenPayment(1, 0, t.a3, value=1*ETH, sender=t.k2))
    # Timeout < now
    assert_tx_failed(t, lambda: uniswap_exchange.ethToTokenPayment(1, timeout - 301, t.a3, value=1*ETH, sender=t.k2))
    # msg.value = 0
    assert_tx_failed(t, lambda: uniswap_exchange.ethToTokenPayment(1, timeout, t.a3, value=0, sender=t.k2))
