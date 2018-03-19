import pytest
from ethereum import utils as u

"""
    run test with:     pytest -v
"""

ETH = 10**18
TOKEN = 10**18

def test_token_to_token_swap(t, uni_token, swap_token, uniswap_factory, exchange_abi, contract_tester, assert_tx_failed):
    t.s.mine()
    # Launch UNI and SWAP exchanges with factory
    uni_exchange_address = uniswap_factory.launchExchange(uni_token.address)
    swap_exchange_address = uniswap_factory.launchExchange(swap_token.address)
    uni_exchange = t.ABIContract(t.s, exchange_abi, uni_exchange_address)
    swap_exchange = t.ABIContract(t.s, exchange_abi, swap_exchange_address)
    t.s.mine()
    # Mint tokens and approve transferFrom for UNI liquidity provider
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.approve(uni_exchange_address, 10*TOKEN, sender=t.k1)
    # Mint tokens and approve transferFrom for SWAP liquidity provider
    swap_token.mint(t.a2, 20*TOKEN)
    swap_token.approve(swap_exchange_address, 20*TOKEN, sender=t.k2)
    # Mint tokens and approve transferFrom for UNI to SWAP buyer
    uni_token.mint(t.a3, 10*TOKEN)
    uni_token.approve(uni_exchange_address, 10*TOKEN, sender=t.k3)
    # UNI provider initializes the exchange with 5 eth and 10 tokens
    uni_exchange.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    # SWAP provider initializes the exchange with 5 eth and 20 tokens
    swap_exchange.initializeExchange(20*TOKEN, value=5*ETH, sender=t.k2)
    timeout = t.s.head_state.timestamp + 300
    t.s.mine()
    # Starting balances of BUYER
    assert t.s.head_state.get_balance(t.a3) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a3) == 10*TOKEN
    assert swap_token.balanceOf(t.a3) == 0
    # BUYER converts  UNI to SWAP
    uni_exchange.tokenToTokenSwap(swap_token.address, 2*TOKEN, 1, timeout, startgas=165000, sender=t.k3)
    # Updated state of UNI exchange
    uni_fee = 4000000000000000                          # 2*TOKEN/500
    uni_new_market_tokens = 11996000000000000000        # 10*TOKEN + 2*TOKEN - uni_fee
    uni_new_market_eth = 4168056018672890963            # (10*TOKEN*5*ETH)/uni_new_market_tokens)
    ETH_TO_TUNNEL = 831943981327109037                  # 5*ETH - uni_new_market_eth
    assert uni_exchange.tokenFees() == uni_fee
    assert uni_exchange.tokenPool() == uni_new_market_tokens
    assert uni_token.balanceOf(uni_exchange.address) == uni_new_market_tokens + uni_fee
    assert uni_exchange.ethPool() == uni_new_market_eth
    assert t.s.head_state.get_balance(uni_exchange.address) == uni_new_market_eth
    # Updated State of SWAP exchange
    swap_fee = 1663887962654218                         # ETH_TO_TUNNEL/500
    swap_new_market_eth = 5830280093364454819           # 5*ETH + ETH_TO_TUNNEL - swap_fee
    swap_new_market_tokens = 17151834628633326487       # (20*TOKEN*5*ETH)/swap_new_market_eth)
    SWAP_TO_BUYER = 2848165371366673513                 # 20*TOKEN - swap_new_market_tokens
    assert swap_exchange.ethFees() == swap_fee
    assert swap_exchange.ethPool() == swap_new_market_eth
    assert swap_exchange.tokenPool() == swap_new_market_tokens
    assert swap_token.balanceOf(swap_exchange.address) == swap_new_market_tokens
    assert t.s.head_state.get_balance(swap_exchange.address) == swap_new_market_eth + swap_fee
    # Final balances of BUYER
    assert t.s.head_state.get_balance(t.a3) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a3) == 8*TOKEN
    assert swap_token.balanceOf(t.a3) == SWAP_TO_BUYER
    # Min tokens = 0
    assert_tx_failed(t, lambda: uni_exchange.tokenToTokenSwap(swap_token.address, 2*TOKEN, 0, timeout, sender=t.k3))
    # Purchased tokens < min tokens
    assert_tx_failed(t, lambda: uni_exchange.tokenToTokenSwap(swap_token.address, 2*TOKEN, 5*TOKEN, timeout, sender=t.k3))
    # Tokens Sold = 0
    assert_tx_failed(t, lambda: uni_exchange.tokenToTokenSwap(swap_token.address, 0, 1, timeout, sender=t.k3))
    # Buyer does not have enough tokens
    assert_tx_failed(t, lambda: uni_exchange.tokenToTokenSwap(swap_token.address, 11*TOKEN, 1, timeout, sender=t.k3))
    # Provided address is the same as the token in the exchange
    assert_tx_failed(t, lambda: uni_exchange.tokenToTokenSwap(uni_token.address, 2*TOKEN, 1, timeout, sender=t.k3))
    # Provided address is the same as the address of the exchange
    assert_tx_failed(t, lambda: uni_exchange.tokenToTokenSwap(uni_exchange.address, 2*TOKEN, 1, timeout, sender=t.k3))
    # Provided address is the same as the address of the other token exchange
    assert_tx_failed(t, lambda: uni_exchange.tokenToTokenSwap(swap_exchange.address, 2*TOKEN, 1, timeout, sender=t.k3))


def test_token_to_token_payment(t, uni_token, swap_token, uniswap_factory, exchange_abi, contract_tester, assert_tx_failed):
    t.s.mine()
    # Create UNI and SWAP token exchanges using uniswap factory
    uni_exchange_address = uniswap_factory.launchExchange(uni_token.address)
    uni_exchange = t.ABIContract(t.s, exchange_abi, uni_exchange_address)
    swap_exchange_address = uniswap_factory.launchExchange(swap_token.address)
    swap_exchange = t.ABIContract(t.s, exchange_abi, swap_exchange_address)
    t.s.mine()
    # Mint tokens and approve transferFrom for UNI liquidity provider
    uni_token.mint(t.a1, 10*TOKEN)
    uni_token.approve(uni_exchange_address, 10*TOKEN, sender=t.k1)
    # Mint tokens and approve transferFrom for SWAP liquidity provider
    swap_token.mint(t.a2, 20*TOKEN)
    swap_token.approve(swap_exchange_address, 20*TOKEN, sender=t.k2)
    # Mint tokens and approve transferFrom for UNI to SWAP buyer
    uni_token.mint(t.a3, 10*TOKEN)
    uni_token.approve(uni_exchange_address, 10*TOKEN, sender=t.k3)
    # UNI provider initializes the exchange with 5 eth and 10 tokens
    uni_exchange.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
    # SWAP provider initializes the exchange with 5 eth and 10 tokens
    swap_exchange.initializeExchange(20*TOKEN, value=5*ETH, sender=t.k2)
    timeout = t.s.head_state.timestamp + 300
    t.s.mine()
    # Starting balances of BUYER
    assert t.s.head_state.get_balance(t.a3) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a3) == 10*TOKEN
    assert swap_token.balanceOf(t.a3) == 0
    # Starting balances of RECIPIENT
    assert t.s.head_state.get_balance(t.a4) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a4) == 0
    assert swap_token.balanceOf(t.a4) == 0
    # BUYER sends UNI and RECIPIENT receives SWAP
    uni_exchange.tokenToTokenPayment(swap_token.address, t.a4, 2*TOKEN, 1, timeout, sender=t.k3)
    # Updated state of UNI exchange
    uni_fee = 4000000000000000                          # 2*TOKEN/500
    uni_new_market_tokens = 11996000000000000000        # 10*TOKEN + 2*TOKEN - uni_fee
    uni_new_market_eth = 4168056018672890963            # (10*TOKEN*5*ETH)/uni_new_market_tokens)
    ETH_TO_TUNNEL = 831943981327109037                  # 5*ETH - uni_new_market_eth
    assert uni_exchange.tokenFees() == uni_fee
    assert uni_exchange.tokenPool() == uni_new_market_tokens
    assert uni_token.balanceOf(uni_exchange.address) == uni_new_market_tokens + uni_fee
    assert uni_exchange.ethPool() == uni_new_market_eth
    assert t.s.head_state.get_balance(uni_exchange.address) == uni_new_market_eth
    # Updated State of SWAP exchange
    swap_fee = 1663887962654218                         # ETH_TO_TUNNEL/500
    swap_new_market_eth = 5830280093364454819           # 5*ETH + ETH_TO_TUNNEL - swap_fee
    swap_new_market_tokens = 17151834628633326487       # (20*TOKEN*5*ETH)/swap_new_market_eth)
    SWAP_TO_BUYER = 2848165371366673513                 # 20*TOKEN - swap_new_market_tokens
    assert swap_exchange.ethFees() == swap_fee
    assert swap_exchange.ethPool() == swap_new_market_eth
    assert swap_exchange.tokenPool() == swap_new_market_tokens
    assert swap_token.balanceOf(swap_exchange.address) == swap_new_market_tokens
    assert t.s.head_state.get_balance(swap_exchange.address) == swap_new_market_eth + swap_fee
    # Final balances of BUYER
    assert t.s.head_state.get_balance(t.a3) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a3) == 8*TOKEN
    assert swap_token.balanceOf(t.a3) == 0
    # Final balances of RECIPIENT
    assert t.s.head_state.get_balance(t.a4) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a4) == 0
    assert swap_token.balanceOf(t.a4) == SWAP_TO_BUYER
    # Min tokens = 0
    assert_tx_failed(t, lambda: uni_exchange.tokenToTokenSwap(swap_token.address, 2*TOKEN, 0, timeout, sender=t.k3))
    # Purchased tokens < min tokens
    assert_tx_failed(t, lambda: uni_exchange.tokenToTokenSwap(swap_token.address, 2*TOKEN, 5*TOKEN, timeout, sender=t.k3))
    # Tokens Sold = 0
    assert_tx_failed(t, lambda: uni_exchange.tokenToTokenSwap(swap_token.address, 0, 1, timeout, sender=t.k3))
    # Buyer does not have enough tokens
    assert_tx_failed(t, lambda: uni_exchange.tokenToTokenSwap(swap_token.address, 11*TOKEN, 1, timeout, sender=t.k3))
    # Provided address is the same as the token in the exchange
    assert_tx_failed(t, lambda: uni_exchange.tokenToTokenSwap(uni_token.address, 2*TOKEN, 1, timeout, sender=t.k3))
    # Provided address is the same as the address of the exchange
    assert_tx_failed(t, lambda: uni_exchange.tokenToTokenSwap(uni_exchange.address, 2*TOKEN, 1, timeout, sender=t.k3))
    # Provided address is the same as the address of the other token exchange
    assert_tx_failed(t, lambda: uni_exchange.tokenToTokenSwap(swap_exchange.address, 2*TOKEN, 1, timeout, sender=t.k3))
