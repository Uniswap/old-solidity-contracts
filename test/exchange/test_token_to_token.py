import pytest
from ethereum import utils as u

"""
    run test with:     pytest -v
"""

DECIMALS = 10**18

def test_token_to_token_swap(t, uni_token, swap_token, uni_token_exchange, swap_token_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    # Mint tokens and approve transferFrom for UNI liquidity provider
    uni_token.mint(t.a1, 10*DECIMALS)
    uni_token.approve(uni_token_exchange.address, 10*DECIMALS, sender=t.k1)
    # Mint tokens and approve transferFrom for SWAP liquidity provider
    swap_token.mint(t.a2, 20*DECIMALS)
    swap_token.approve(swap_token_exchange.address, 20*DECIMALS, sender=t.k2)
    # Mint tokens and approve transferFrom for UNI to SWAP buyer
    uni_token.mint(t.a3, 10*DECIMALS)
    uni_token.approve(uni_token_exchange.address, 10*DECIMALS, sender=t.k3)
    # UNI provider initializes the exchange with 5 eth and 10 tokens
    uni_token_exchange.initializeExchange(10*DECIMALS, value=5*DECIMALS, sender=t.k1)
    # SWAP provider initializes the exchange with 5 eth and 20 tokens
    swap_token_exchange.initializeExchange(20*DECIMALS, value=5*DECIMALS, sender=t.k2)
    timeout = t.s.head_state.timestamp + 300
    t.s.mine()
    # Starting balances of BUYER
    assert t.s.head_state.get_balance(t.a3) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a3) == 10*DECIMALS
    assert swap_token.balanceOf(t.a3) == 0
    # BUYER converts  UNI to SWAP
    uni_token_exchange.tokenToTokenSwap(swap_token.address, 2*DECIMALS, 1, timeout, startgas=165000, sender=t.k3)
    # Updated state of UNI exchange
    uni_fee = 4000000000000000                          # 2*DECIMALS/500
    uni_new_market_tokens = 11996000000000000000        # 10*DECIMALS + 2*DECIMALS - uni_fee
    uni_new_market_eth = 4168056018672890963            # (10*DECIMALS*5*DECIMALS)/uni_new_market_tokens)
    ETH_TO_TUNNEL = 831943981327109037                  # 5*DECIMALS - uni_new_market_eth
    assert uni_token_exchange.tokenFees() == uni_fee
    assert uni_token_exchange.tokenPool() == uni_new_market_tokens
    assert uni_token.balanceOf(uni_token_exchange.address) == uni_new_market_tokens + uni_fee
    assert uni_token_exchange.ethPool() == uni_new_market_eth
    assert t.s.head_state.get_balance(uni_token_exchange.address) == uni_new_market_eth
    # Updated State of SWAP exchange
    swap_fee = 1663887962654218                         # ETH_TO_TUNNEL/500
    swap_new_market_eth = 5830280093364454819           # 5*DECIMALS + ETH_TO_TUNNEL - swap_fee
    swap_new_market_tokens = 17151834628633326487       # (20*DECIMALS*5*DECIMALS)/swap_new_market_eth)
    SWAP_TO_BUYER = 2848165371366673513                 # 20*DECIMALS - swap_new_market_tokens
    assert swap_token_exchange.ethFees() == swap_fee
    assert swap_token_exchange.ethPool() == swap_new_market_eth
    assert swap_token_exchange.tokenPool() == swap_new_market_tokens
    assert swap_token.balanceOf(swap_token_exchange.address) == swap_new_market_tokens
    assert t.s.head_state.get_balance(swap_token_exchange.address) == swap_new_market_eth + swap_fee
    # Final balances of BUYER
    assert t.s.head_state.get_balance(t.a3) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a3) == 8*DECIMALS
    assert swap_token.balanceOf(t.a3) == SWAP_TO_BUYER
    # Min tokens = 0
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToTokenSwap(swap_token.address, 2*DECIMALS, 0, timeout, sender=t.k3))
    # Purchased tokens < min tokens
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToTokenSwap(swap_token.address, 2*DECIMALS, 5*DECIMALS, timeout, sender=t.k3))
    # Tokens Sold = 0
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToTokenSwap(swap_token.address, 0, 1, timeout, sender=t.k3))
    # Buyer does not have enough tokens
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToTokenSwap(swap_token.address, 11*DECIMALS, 1, timeout, sender=t.k3))
    # Provided address is the same as the token in the exchange
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToTokenSwap(uni_token.address, 2*DECIMALS, 1, timeout, sender=t.k3))
    # Provided address is the same as the address of the exchange
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToTokenSwap(uni_token_exchange.address, 2*DECIMALS, 1, timeout, sender=t.k3))
    # Provided address is the same as the address of the other token exchange
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToTokenSwap(swap_token_exchange.address, 2*DECIMALS, 1, timeout, sender=t.k3))


def test_token_to_token_payment(t, uni_token, swap_token, uni_token_exchange, swap_token_exchange, contract_tester, assert_tx_failed):
    t.s.mine()
    # Mint tokens and approve transferFrom for UNI liquidity provider
    uni_token.mint(t.a1, 10*DECIMALS)
    uni_token.approve(uni_token_exchange.address, 10*DECIMALS, sender=t.k1)
    # Mint tokens and approve transferFrom for SWAP liquidity provider
    swap_token.mint(t.a2, 20*DECIMALS)
    swap_token.approve(swap_token_exchange.address, 20*DECIMALS, sender=t.k2)
    # Mint tokens and approve transferFrom for UNI to SWAP buyer
    uni_token.mint(t.a3, 10*DECIMALS)
    uni_token.approve(uni_token_exchange.address, 10*DECIMALS, sender=t.k3)
    # UNI provider initializes the exchange with 5 eth and 10 tokens
    uni_token_exchange.initializeExchange(10*DECIMALS, value=5*DECIMALS, sender=t.k1)
    # SWAP provider initializes the exchange with 5 eth and 10 tokens
    swap_token_exchange.initializeExchange(20*DECIMALS, value=5*DECIMALS, sender=t.k2)
    timeout = t.s.head_state.timestamp + 300
    t.s.mine()
    # Starting balances of BUYER
    assert t.s.head_state.get_balance(t.a3) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a3) == 10*DECIMALS
    assert swap_token.balanceOf(t.a3) == 0
    # Starting balances of RECIPIENT
    assert t.s.head_state.get_balance(t.a4) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a4) == 0
    assert swap_token.balanceOf(t.a4) == 0
    # BUYER sends UNI and RECIPIENT receives SWAP
    uni_token_exchange.tokenToTokenPayment(swap_token.address, t.a4, 2*DECIMALS, 1, timeout, sender=t.k3)
    # Updated state of UNI exchange
    uni_fee = 4000000000000000                          # 2*DECIMALS/500
    uni_new_market_tokens = 11996000000000000000        # 10*DECIMALS + 2*DECIMALS - uni_fee
    uni_new_market_eth = 4168056018672890963            # (10*DECIMALS*5*DECIMALS)/uni_new_market_tokens)
    ETH_TO_TUNNEL = 831943981327109037                  # 5*DECIMALS - uni_new_market_eth
    assert uni_token_exchange.tokenFees() == uni_fee
    assert uni_token_exchange.tokenPool() == uni_new_market_tokens
    assert uni_token.balanceOf(uni_token_exchange.address) == uni_new_market_tokens + uni_fee
    assert uni_token_exchange.ethPool() == uni_new_market_eth
    assert t.s.head_state.get_balance(uni_token_exchange.address) == uni_new_market_eth
    # Updated State of SWAP exchange
    swap_fee = 1663887962654218                         # ETH_TO_TUNNEL/500
    swap_new_market_eth = 5830280093364454819           # 5*DECIMALS + ETH_TO_TUNNEL - swap_fee
    swap_new_market_tokens = 17151834628633326487       # (20*DECIMALS*5*DECIMALS)/swap_new_market_eth)
    SWAP_TO_BUYER = 2848165371366673513                 # 20*DECIMALS - swap_new_market_tokens
    assert swap_token_exchange.ethFees() == swap_fee
    assert swap_token_exchange.ethPool() == swap_new_market_eth
    assert swap_token_exchange.tokenPool() == swap_new_market_tokens
    assert swap_token.balanceOf(swap_token_exchange.address) == swap_new_market_tokens
    assert t.s.head_state.get_balance(swap_token_exchange.address) == swap_new_market_eth + swap_fee
    # Final balances of BUYER
    assert t.s.head_state.get_balance(t.a3) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a3) == 8*DECIMALS
    assert swap_token.balanceOf(t.a3) == 0
    # Final balances of RECIPIENT
    assert t.s.head_state.get_balance(t.a4) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a4) == 0
    assert swap_token.balanceOf(t.a4) == SWAP_TO_BUYER
    # Min tokens = 0
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToTokenSwap(swap_token.address, 2*DECIMALS, 0, timeout, sender=t.k3))
    # Purchased tokens < min tokens
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToTokenSwap(swap_token.address, 2*DECIMALS, 5*DECIMALS, timeout, sender=t.k3))
    # Tokens Sold = 0
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToTokenSwap(swap_token.address, 0, 1, timeout, sender=t.k3))
    # Buyer does not have enough tokens
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToTokenSwap(swap_token.address, 11*DECIMALS, 1, timeout, sender=t.k3))
    # Provided address is the same as the token in the exchange
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToTokenSwap(uni_token.address, 2*DECIMALS, 1, timeout, sender=t.k3))
    # Provided address is the same as the address of the exchange
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToTokenSwap(uni_token_exchange.address, 2*DECIMALS, 1, timeout, sender=t.k3))
    # Provided address is the same as the address of the other token exchange
    assert_tx_failed(t, lambda: uni_token_exchange.tokenToTokenSwap(swap_token_exchange.address, 2*DECIMALS, 1, timeout, sender=t.k3))
