import pytest
from ethereum import utils as u

"""
    run test with:     pytest -v
"""

def test_initial_state(t, uni_token, contract_tester, assert_tx_failed):
    assert uni_token.name().decode("utf-8") == 'UNI Token'
    assert uni_token.symbol().decode("utf-8") == 'UNI'
    assert uni_token.decimals() == 18
    assert uni_token.totalSupply() ==0

def test_mint(t, uni_token, assert_tx_failed):
    # Mint fails if not called by contact owner
    assert_tx_failed(t, lambda: uni_token.mint(t.a2, 100*10**12, sender=t.k2))
    # Mint tokens for 3 accounts
    assert uni_token.balanceOf(t.a0) == 0
    uni_token.mint(t.a1, 100*10**18)
    uni_token.mint(t.a2, 200*10**18)
    assert uni_token.balanceOf(t.a1) == 100*10**18
    assert uni_token.balanceOf(t.a2) == 200*10**18
    assert uni_token.totalSupply() == 100*10**18 + 200*10**18
