import pytest
from ethereum import utils as u

@pytest.fixture
def uni_token(t, contract_tester):
    return contract_tester('Token/UniToken.sol', args=[])

def test_initial_state(t, uni_token, contract_tester, assert_tx_failed):
    assert uni_token.decimals() == 12;

def test_mint_tokens(t, uni_token, assert_tx_failed):
    assert uni_token.balanceOf(t.a0) == 0;
    uni_token.mint(t.a0, 100*10**12)
    assert uni_token.balanceOf(t.a0) == 100*10**12;

    
