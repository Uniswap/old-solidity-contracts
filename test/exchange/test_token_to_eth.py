import pytest
from ethereum import utils as u

"""
    run test with:     pytest -v
"""

DECIMALS = 10**18

def test_tokens_to_eth_swap(t, uni_token, uni_token_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*DECIMALS)
    uni_token.mint(t.a2, 2*DECIMALS)
    uni_token.approve(uni_token_exchange.address, 10*DECIMALS, sender=t.k1)
    uni_token.approve(uni_token_exchange.address, 2*DECIMALS, sender=t.k2)
    # PROVIDER initializes exchange
    uni_token_exchange.initializeExchange(10*DECIMALS, value=5*DECIMALS, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    # Starting balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a2) == 2*DECIMALS
    # BUYER converts UNI to ETH
    uni_token_exchange.tokenToEthSwap(2*DECIMALS, 1, timeout, sender=t.k2)
    # Updated balances of UNI exchange
    fee = 4000000000000000                        # fee = 2*DECIMALS/500
    new_market_tokens = 11996000000000000000      # new_market_tokens = 10*DECIMALS + 2*DECIMALS - fee
    new_market_eth = 4168056018672890963          # new_market_eth = (5*DECIMALS*10*DECIMALS)/new_market_tokens
    purchased_eth =  831943981327109037           # purchased_eth = 5*DECIMALS - new_market_eth
    assert uni_token_exchange.tokenFees() == fee
    assert uni_token_exchange.tokenPool() == new_market_tokens
    assert uni_token.balanceOf(uni_token_exchange.address) == new_market_tokens + fee
    assert uni_token_exchange.ethPool() == new_market_eth
    assert t.s.head_state.get_balance(uni_token_exchange.address) == new_market_eth
    # Final balances of BUYER
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000 + purchased_eth
    assert uni_token.balanceOf(t.a2) == 0
    # Tokens sold = 0
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(0, 1, timeout, sender=t.k2))
    # Tokens sold > balances[msg.sender]
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(3*DECIMALS, 1, timeout, sender=t.k2))
    # Min eth = 0
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(2*DECIMALS, 0, timeout, sender=t.k2))
    # Purchased ETH < min ETH
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(2*DECIMALS, purchased_eth + 1, timeout, sender=t.k2))
    # Timeout = 0
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(2*DECIMALS, 1, 0, sender=t.k2))
    # Timeout < now
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(2*DECIMALS, 1, timeout - 301, sender=t.k2))

def test_tokens_to_eth_payment(t, uni_token, uni_token_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    uni_token.mint(t.a1, 10*DECIMALS)
    uni_token.mint(t.a2, 2*DECIMALS)
    uni_token.approve(uni_token_exchange.address, 10*DECIMALS, sender=t.k1)
    uni_token.approve(uni_token_exchange.address, 2*DECIMALS, sender=t.k2)
    # PROVIDER initializes exchange
    uni_token_exchange.initializeExchange(10*DECIMALS, value=5*DECIMALS, sender=t.k1)
    timeout = t.s.head_state.timestamp + 300
    # Starting balances of SENDER (t.a2) and RECIPIENT (t.a3)
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a2) == 2*DECIMALS
    assert t.s.head_state.get_balance(t.a3) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a3) == 0
    # SENDER pays UNI and RECIPIENT receives ETH
    uni_token_exchange.tokenToEthPayment(2*DECIMALS, 1, timeout, t.a3, sender=t.k2)
    # Updated balances of UNI exchange
    fee = 4000000000000000                        # fee = 2*DECIMALS/500
    new_market_tokens = 11996000000000000000      # new_market_tokens = 10*DECIMALS + 2*DECIMALS - fee
    new_market_eth = 4168056018672890963          # new_market_eth = (5*DECIMALS*10*DECIMALS)/new_market_tokens
    purchased_eth =  831943981327109037           # purchased_eth = 5*DECIMALS - new_market_eth
    assert uni_token_exchange.tokenFees() == fee
    assert uni_token_exchange.tokenPool() == new_market_tokens
    assert uni_token.balanceOf(uni_token_exchange.address) == new_market_tokens + fee
    assert uni_token_exchange.ethPool() == new_market_eth
    assert t.s.head_state.get_balance(uni_token_exchange.address) == new_market_eth
    # Final balances of SENDER and RECIPIENT
    assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a2) == 0
    assert t.s.head_state.get_balance(t.a3) == 1000000000000000000000000000000 + purchased_eth
    assert uni_token.balanceOf(t.a3) == 0
    # Tokens sold = 0
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(0, 1, timeout, sender=t.k2))
    # Tokens sold > balances[msg.sender]
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(3*DECIMALS, 1, timeout, sender=t.k2))
    # Min eth = 0
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(2*DECIMALS, 0, timeout, sender=t.k2))
    # Purchased ETH < min ETH
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(2*DECIMALS, purchased_eth + 1, timeout, sender=t.k2))
    # Timeout = 0
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(2*DECIMALS, 1, 0, sender=t.k2))
    # Timeout < now
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToEthSwap(2*DECIMALS, 1, timeout - 301, sender=t.k2))
