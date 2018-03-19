import pytest
from ethereum import utils as u

"""
    run test with:     pytest -v
"""

ETH = 10**18
TOKEN = 10**18

def test_tokens_to_eth_swap(t, uni_token, uniswap_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.mint(t.a2, 2*TOKEN)
    uni_token.approve(uniswap_exchange.address, 10*TOKEN, sender=t.k1)
    uni_token.approve(uniswap_exchange.address, 2*TOKEN, sender=t.k2)
    # PROVIDER initializes exchange
    uniswap_exchange.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    # Starting balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a2) == 2*TOKEN
    # BUYER converts UNI to ETH
    uniswap_exchange.tokenToEthSwap(2*TOKEN, 1, timeout, sender=t.k2)
    # Updated balances of UNI exchange
    fee = 4000000000000000                        # fee = 2*TOKEN/500
    new_market_tokens = 11996000000000000000      # new_market_tokens = 10*TOKEN + 2*TOKEN - fee
    new_market_eth = 4168056018672890963          # new_market_eth = (5*ETH*10*TOKEN)/new_market_tokens
    purchased_eth =  831943981327109037           # purchased_eth = 5*ETH - new_market_eth
    assert uniswap_exchange.tokenFees() == fee
    assert uniswap_exchange.tokenPool() == new_market_tokens
    assert uni_token.balanceOf(uniswap_exchange.address) == new_market_tokens + fee
    assert uniswap_exchange.ethPool() == new_market_eth
    assert t.s.head_state.get_balance(uniswap_exchange.address) == new_market_eth
    # Final balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000 + purchased_eth
    assert uni_token.balanceOf(t.a2) == 0
    # Tokens sold = 0
    assert_tx_failed(t, lambda: uniswap_exchange.tokenToEthSwap(0, 1, timeout, sender=t.k2))
    # Tokens sold > balances[msg.sender]
    assert_tx_failed(t, lambda: uniswap_exchange.tokenToEthSwap(3*TOKEN, 1, timeout, sender=t.k2))
    # Min eth = 0
    assert_tx_failed(t, lambda: uniswap_exchange.tokenToEthSwap(2*TOKEN, 0, timeout, sender=t.k2))
    # Purchased ETH < min ETH
    assert_tx_failed(t, lambda: uniswap_exchange.tokenToEthSwap(2*TOKEN, purchased_eth + 1, timeout, sender=t.k2))
    # Timeout = 0
    assert_tx_failed(t, lambda: uniswap_exchange.tokenToEthSwap(2*TOKEN, 1, 0, sender=t.k2))
    # Timeout < now
    assert_tx_failed(t, lambda: uniswap_exchange.tokenToEthSwap(2*TOKEN, 1, timeout - 301, sender=t.k2))

def test_tokens_to_eth_payment(t, uni_token, uniswap_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.mint(t.a2, 2*TOKEN)
    uni_token.approve(uniswap_exchange.address, 10*TOKEN, sender=t.k1)
    uni_token.approve(uniswap_exchange.address, 2*TOKEN, sender=t.k2)
    # PROVIDER initializes exchange
    uniswap_exchange.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    # Starting balances of SENDER (t.a2) and RECIPIENT (t.a3)
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a2) == 2*TOKEN
    assert t.s.head_state.get_balance(t.a3) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a3) == 0
    # SENDER pays UNI and RECIPIENT receives ETH
    uniswap_exchange.tokenToEthPayment(2*TOKEN, 1, timeout, t.a3, sender=t.k2)
    # Updated balances of UNI exchange
    fee = 4000000000000000                        # fee = 2*TOKEN/500
    new_market_tokens = 11996000000000000000      # new_market_tokens = 10*TOKEN + 2*TOKEN - fee
    new_market_eth = 4168056018672890963          # new_market_eth = (5*ETH*10*TOKEN)/new_market_tokens
    purchased_eth =  831943981327109037           # purchased_eth = 5*ETH - new_market_eth
    assert uniswap_exchange.tokenFees() == fee
    assert uniswap_exchange.tokenPool() == new_market_tokens
    assert uni_token.balanceOf(uniswap_exchange.address) == new_market_tokens + fee
    assert uniswap_exchange.ethPool() == new_market_eth
    assert t.s.head_state.get_balance(uniswap_exchange.address) == new_market_eth
    # Final balances of SENDER and RECIPIENT
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a2) == 0
    assert t.s.head_state.get_balance(t.a3) == 1000000000000000000000000000000 + purchased_eth
    assert uni_token.balanceOf(t.a3) == 0
    # Tokens sold = 0
    assert_tx_failed(t, lambda: uniswap_exchange.tokenToEthSwap(0, 1, timeout, sender=t.k2))
    # Tokens sold > balances[msg.sender]
    assert_tx_failed(t, lambda: uniswap_exchange.tokenToEthSwap(3*TOKEN, 1, timeout, sender=t.k2))
    # Min eth = 0
    assert_tx_failed(t, lambda: uniswap_exchange.tokenToEthSwap(2*TOKEN, 0, timeout, sender=t.k2))
    # Purchased ETH < min ETH
    assert_tx_failed(t, lambda: uniswap_exchange.tokenToEthSwap(2*TOKEN, purchased_eth + 1, timeout, sender=t.k2))
    # Timeout = 0
    assert_tx_failed(t, lambda: uniswap_exchange.tokenToEthSwap(2*TOKEN, 1, 0, sender=t.k2))
    # Timeout < now
    assert_tx_failed(t, lambda: uniswap_exchange.tokenToEthSwap(2*TOKEN, 1, timeout - 301, sender=t.k2))
