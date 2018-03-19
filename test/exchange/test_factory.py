import pytest
from ethereum import utils as u

"""
    run test with:     pytest -v
"""

ETH = 10**18
TOKEN = 10**18

def test_uniswap_factory(t, uni_token, swap_token, uniswap_factory, exchange_abi, contract_tester, assert_tx_failed):
    t.s.mine()
    # Launch UNI Exchange
    uni_exchange_address = uniswap_factory.launchExchange(uni_token.address)
    uni_token_exchange = t.ABIContract(t.s, exchange_abi, uni_exchange_address)
    assert uniswap_factory.getExchangeCount() == 1
    assert uni_exchange_address == uniswap_factory.tokenToExchangeLookup(uni_token.address)
    assert uniswap_factory.tokenToExchangeLookup(uni_token.address) == uni_exchange_address
    assert  u.remove_0x_head(uniswap_factory.exchangeToTokenLookup(uni_exchange_address)) == uni_token.address.hex()
    # Test exchange initial state
    assert uni_token_exchange.FEE_RATE() == 500
    assert uni_token_exchange.ethPool() == 0
    assert uni_token_exchange.tokenPool() == 0
    assert uni_token_exchange.invariant() == 0
    assert uni_token_exchange.ethFees() == 0
    assert uni_token_exchange.tokenFees() == 0
    assert u.remove_0x_head(uni_token_exchange.tokenAddress()) == uni_token.address.hex()
    assert uni_token_exchange.totalShares() == 0
    t.s.mine()
    # Launch SWAP Exchange
    swap_exchange_address = uniswap_factory.launchExchange(swap_token.address)
    swap_token_exchange = t.ABIContract(t.s, exchange_abi, swap_exchange_address)
    assert uniswap_factory.getExchangeCount() == 2
    assert swap_exchange_address == uniswap_factory.tokenToExchangeLookup(swap_token.address)
    assert uniswap_factory.tokenToExchangeLookup(swap_token.address) == swap_exchange_address
    assert  u.remove_0x_head(uniswap_factory.exchangeToTokenLookup(swap_exchange_address)) == swap_token.address.hex()
    # launch exchange fails if sent ether
    assert_tx_failed(t, lambda: uniswap_factory.launchExchange(uni_token.address, value=10))
    # launch exchange fails if parameters are missing
    assert_tx_failed(t, lambda: uniswap_factory.launchExchange())
    # launch exxchange fails if token address is 0x0
    assert_tx_failed(t, lambda: uniswap_factory.launchExchange('0000000000000000000000000000000000000000'))
