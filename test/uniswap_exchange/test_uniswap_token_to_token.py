import pytest
from ethereum import utils as u
import json
import os

"""
    run test with:     python3.6 -m pytest -v
"""

ETH = 10**18
TOKEN = 10**12
EXCHANGE_ABI = os.path.join(os.path.dirname(__file__), '../ABI/exchangeABI.json')

@pytest.fixture
def uni_token(t, contract_tester):
    return contract_tester('Token/UniToken.sol', args=[])

@pytest.fixture
def swap_token(t, contract_tester):
    return contract_tester('Token/SwapToken.sol', args=[])

@pytest.fixture
def uniswap_factory(t, contract_tester):
    return contract_tester('Exchange/UniswapFactory.sol', args=[])

def test_token_to_token(t, uni_token, swap_token, uniswap_factory, contract_tester, assert_tx_failed):
    t.s.mine()
    abi = json.load(open(EXCHANGE_ABI))
    # Create UNI and SWAP token exchanges using uniswap factory
    uni_exchange_address = uniswap_factory.createExchange(uni_token.address)
    uni_exchange = t.ABIContract(t.s, abi, uni_exchange_address)
    swap_exchange_address = uniswap_factory.createExchange(swap_token.address)
    swap_exchange = t.ABIContract(t.s, abi, swap_exchange_address)
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
    UNI_INVARIANT = 5*ETH*10*TOKEN
    # SWAP provider initializes the exchange with 5 eth and 10 tokens
    swap_exchange.initializeExchange(20*TOKEN, value=5*ETH, sender=t.k2)
    SWAP_INVARIANT = 5*ETH*20*TOKEN
    t.s.mine()
    # Starting balances of BUYER
    assert t.s.head_state.get_balance(t.a3) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a3) == 10*TOKEN
    assert swap_token.balanceOf(t.a3) == 0
    # BUYER converts  UNI to SWAP
    uni_exchange.tokenToEthToTunnel(swap_token.address, 2*TOKEN, sender=t.k3)
    # Updated state of UNI exchange
    uni_fee = 2*TOKEN/500
    uni_new_market_tokens = 10*TOKEN + 2*TOKEN - uni_fee
    uni_new_market_eth = int(UNI_INVARIANT/uni_new_market_tokens)
    ETH_TO_TUNNEL = 5*ETH - uni_new_market_eth
    assert uni_exchange.tokenFeePool() == uni_fee
    assert uni_exchange.tokensInMarket() == uni_new_market_tokens
    assert uni_token.balanceOf(uni_exchange.address) == uni_new_market_tokens + uni_fee
    assert uni_exchange.ethInMarket() == uni_new_market_eth - 429      # rounding error = 429 wei
    assert t.s.head_state.get_balance(uni_exchange.address) == uni_new_market_eth - 429        # rounding error = 429 wei
    # Updated State of SWAP exchange
    swap_fee = int(ETH_TO_TUNNEL/500)
    swap_new_market_eth = 5*ETH + ETH_TO_TUNNEL - swap_fee
    swap_new_market_tokens = int(SWAP_INVARIANT/swap_new_market_eth)
    SWAP_TO_BUYER = 20*TOKEN - swap_new_market_tokens
    assert swap_exchange.ethFeePool() == swap_fee + 1               # rounding error = 1 wei
    assert swap_exchange.ethInMarket() == swap_new_market_eth + 428     # rounding error = 428 wei
    assert swap_exchange.tokensInMarket() == swap_new_market_tokens
    assert swap_token.balanceOf(swap_exchange.address) == swap_new_market_tokens
    assert t.s.head_state.get_balance(swap_exchange.address) == swap_new_market_eth + swap_fee + 429  # exchange gains 429 wei due to rounding error
    # Final balances of BUYER
    assert t.s.head_state.get_balance(t.a3) == 1000000000000000000000000000000
    assert uni_token.balanceOf(t.a3) == 8*TOKEN
    assert swap_token.balanceOf(t.a3) == SWAP_TO_BUYER


    '''
    Rounding error is minimmal
    '''
