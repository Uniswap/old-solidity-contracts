import pytest
from ethereum import utils as u

"""
    run test with:     python3.6 -m pytest
"""

@pytest.fixture
def uni_token(t, contract_tester):
    return contract_tester('Token/UniToken.sol', args=[])

@pytest.fixture
def uniswap_multi(t, contract_tester, uni_token):
    return contract_tester('Exchange/UniswapMultipleProviders.sol', args=[uni_token.address])

def test_token_initial_state(t, uni_token, contract_tester, assert_tx_failed):
    assert uni_token.decimals() == 12;

def test_mint_tokens(t, uni_token, assert_tx_failed):
    assert uni_token.balanceOf(t.a0) == 0;
    uni_token.mint(t.a0, 100*10**12)
    assert uni_token.balanceOf(t.a0) == 100*10**12;
    assert uni_token.totalSupply() == 100*10**12;

def test_exchange_initial_state(t, uni_token, uniswap_multi, contract_tester, assert_tx_failed):
    assert uniswap_multi.invariant() == 0;
    assert uniswap_multi.ethInMarket() == 0;
    assert uniswap_multi.tokensInMarket() == 0;
    assert u.remove_0x_head(uniswap_multi.tokenAddress()) == uni_token.address.hex();
