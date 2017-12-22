import pytest
from ethereum import utils as u

"""
    run test with:     python3.6 -m pytest
"""

TOKEN_VALUE_1 = 100*10**12
TOKEN_VALUE_2 = 200*10**12
TOKEN_VALUE_3 = 300*10**12

@pytest.fixture
def uni_token(t, contract_tester):
    return contract_tester('Token/UniToken.sol', args=[])

def test_initial_state(t, uni_token, contract_tester, assert_tx_failed):
    assert uni_token.name().decode("utf-8") == 'UNI Test Token'
    assert uni_token.symbol().decode("utf-8") == 'UNI'
    assert uni_token.decimals() == 12;
    
def test_mint_tokens(t, uni_token, assert_tx_failed):
    # Mint fails if not called by contact owner
    assert_tx_failed(t, lambda: uni_token.mint(t.a2, 100*10**12, sender=t.k2))
    # Mint tokens for 3 accounts
    assert uni_token.balanceOf(t.a0) == 0
    uni_token.mint(t.a1, TOKEN_VALUE_1)
    uni_token.mint(t.a2, TOKEN_VALUE_2)
    uni_token.mint(t.a3, TOKEN_VALUE_3)
    assert uni_token.balanceOf(t.a1) == TOKEN_VALUE_1
    assert uni_token.balanceOf(t.a2) == TOKEN_VALUE_2
    assert uni_token.balanceOf(t.a3) == TOKEN_VALUE_3
    assert uni_token.totalSupply() == TOKEN_VALUE_1 + TOKEN_VALUE_2 + TOKEN_VALUE_3
