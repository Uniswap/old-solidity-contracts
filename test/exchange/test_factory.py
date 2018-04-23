def test_factory(t, utils, uni_token, swap_token, uniswap_factory, exchange_abi, contract_tester, assert_tx_failed):
    # Test initial factory state
    assert uniswap_factory.getExchangeCount() == 0
    # Launch UNI Exchange
    t.s.mine()
    uni_exchange_address = uniswap_factory.launchExchange(uni_token.address)
    uni_token_exchange = t.ABIContract(t.s, exchange_abi, uni_exchange_address)
    # Test new factory state
    assert uniswap_factory.getExchangeCount() == 1
    assert uni_exchange_address == uniswap_factory.tokenToExchangeLookup(uni_token.address)
    assert uniswap_factory.tokenToExchangeLookup(uni_token.address) == uni_exchange_address
    assert  utils.remove_0x_head(uniswap_factory.exchangeToTokenLookup(uni_exchange_address)) == uni_token.address.hex()
    # Test UNI Exchange initial state
    assert uni_token_exchange.FEE_RATE() == 500
    assert uni_token_exchange.ethPool() == 0
    assert uni_token_exchange.tokenPool() == 0
    assert uni_token_exchange.invariant() == 0
    assert uni_token_exchange.totalShares() == 0
    assert utils.remove_0x_head(uni_token_exchange.tokenAddress()) == uni_token.address.hex()
    assert utils.remove_0x_head(uni_token_exchange.factoryAddress()) == uniswap_factory.address.hex()
    # Launch SWAP Exchange
    t.s.mine()
    swap_exchange_address = uniswap_factory.launchExchange(swap_token.address)
    swap_token_exchange = t.ABIContract(t.s, exchange_abi, swap_exchange_address)
    # Test new factory state
    assert uniswap_factory.getExchangeCount() == 2
    assert swap_exchange_address == uniswap_factory.tokenToExchangeLookup(swap_token.address)
    assert uniswap_factory.tokenToExchangeLookup(swap_token.address) == swap_exchange_address
    assert utils.remove_0x_head(uniswap_factory.exchangeToTokenLookup(swap_exchange_address)) == swap_token.address.hex()
    # Test SWAP Exchange initial state
    assert swap_token_exchange.FEE_RATE() == 500
    assert swap_token_exchange.ethPool() == 0
    assert swap_token_exchange.tokenPool() == 0
    assert swap_token_exchange.invariant() == 0
    assert swap_token_exchange.totalShares() == 0
    assert utils.remove_0x_head(swap_token_exchange.tokenAddress()) == swap_token.address.hex()
    assert utils.remove_0x_head(swap_token_exchange.factoryAddress()) == uniswap_factory.address.hex()
    # Launch exchange fails if the exchange already exists
    assert_tx_failed(t, lambda: uniswap_factory.launchExchange(uni_token.address))
    # Launch exchange fails if sent ether
    assert_tx_failed(t, lambda: uniswap_factory.launchExchange(uni_token.address, value=10))
    # Launch exchange fails if parameters are missing
    assert_tx_failed(t, lambda: uniswap_factory.launchExchange())
    # Launch exxchange fails if token address is 0x0
    assert_tx_failed(t, lambda: uniswap_factory.launchExchange('0000000000000000000000000000000000000000'))
