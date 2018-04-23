def test_initial_state(t, uni_token, contract_tester, assert_tx_failed):
    assert uni_token.name().decode("utf-8") == 'UNI Token'
    assert uni_token.symbol().decode("utf-8") == 'UNI'
    assert uni_token.decimals() == 18
    assert uni_token.totalSupply() == 0

def test_mint_transfer(t, uni_token, assert_tx_failed):
    # Mint fails if not called by contact owner
    assert_tx_failed(t, lambda: uni_token.mint(t.a2, 100, sender=t.k2))
    assert uni_token.balanceOf(t.a0) == 0
    uni_token.mint(t.a1, 100)
    uni_token.mint(t.a2, 200)
    assert uni_token.balanceOf(t.a1) == 100
    assert uni_token.balanceOf(t.a2) == 200
    assert uni_token.totalSupply() == 300
    uni_token.transfer(t.a2, 100, sender=t.k1)
    assert uni_token.balanceOf(t.a1) == 0
    assert uni_token.balanceOf(t.a2) == 300
    assert uni_token.totalSupply() == 300
    # transferFrom fails if not approved
    assert_tx_failed(t, lambda: uni_token.transferFrom(t.a2, t.a1, 200, sender=t.k3))
    uni_token.approve(t.a3, 200, sender=t.k2)
    uni_token.transferFrom(t.a2, t.a1, 200, sender=t.k3)
    assert uni_token.balanceOf(t.a1) == 200
    assert uni_token.balanceOf(t.a2) == 100
    assert uni_token.totalSupply() == 300
