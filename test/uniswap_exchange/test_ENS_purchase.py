# import pytest
# from ethereum import utils as u
# from ens import ENS
# from web3 import Web3, IPCProvider
#
# """
#     run test with:     python3.6 -m pytest -v
# """
#
# ETH = 10**18
# TOKEN = 10**12
#
# ens = ENS(IPCProvider('/your/custom/ipc/path'))
#
# # web3 = Web3(IPCProvider())
# # web3.eth.blockNumber 4000000
#
# ens.setup_address('uniswap.eth')
# # ens.setup_address('uniswap.eth', uniswap_multi.address)
#
# @pytest.fixture
# def uni_token(t, contract_tester):
#     return contract_tester('Token/UniToken.sol', args=[])
#
# @pytest.fixture
# def uniswap_multi(t, contract_tester, uni_token):
#     return contract_tester('Exchange/UniswapLiquidityProviders.sol', args=[uni_token.address])
#
#
# def test_ENS_eth_to_tokens(t, uni_token, uniswap_multi, contract_tester, assert_tx_failed):
#     uni_token.mint(t.a1, 10*TOKEN)
#     uni_token.approve(uniswap_multi.address, 10*TOKEN, sender=t.k1)
#     # Initialize exchange
#     uniswap_multi.initializeExchange(10*TOKEN, value=5*ETH, sender=t.k1)
#     timeout = t.s.head_state.timestamp + 300
#     INVARIANT = 5*ETH*10*TOKEN
#     # Starting Balances of buyer address
#     assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000
#     assert uni_token.balanceOf(t.a2) == 0
#     t.s.mine();
#     # ENS setup
#     # ens.setup_address('uniswap.eth', uniswap_multi.address)
#     # Buy Tokens
#     STARTGAS=90000
#     t.s.tx(to=uniswap_multi.address, startgas=STARTGAS, value=1*ETH, sender=t.k2)
#     fee = 1*ETH/500
#     assert uniswap_multi.ethFeePool() == fee
#     new_market_eth = 5*ETH + 1*ETH - fee
#     assert uniswap_multi.ethInMarket() == new_market_eth
#     # Contract ETH balance = eth in market + fee
#     assert t.s.head_state.get_balance(uniswap_multi.address) == new_market_eth + fee
#     new_market_tokens = int(INVARIANT/new_market_eth)
#     assert uniswap_multi.tokensInMarket() == new_market_tokens
#     # Contract Token balance = tokens in market
#     assert uni_token.balanceOf(uniswap_multi.address) == new_market_tokens
#     purchased_tokens = 10*TOKEN - new_market_tokens
#     # Final Balances of buyer address
#     assert t.s.head_state.get_balance(t.a2) == 1000000000000000000000000000000 - 1*ETH
#     assert uni_token.balanceOf(t.a2) == purchased_tokens
#     # msg.value = 0
#     assert_tx_failed(t, lambda: t.s.tx(to=uniswap_multi.address, startgas=STARTGAS, sender=t.k2))
#     # not enough gas
#     assert_tx_failed(t, lambda: t.s.tx(to=uniswap_multi.address, startgas=21000, value=1*ETH, sender=t.k2))
#     # msg.value is too high
#     assert_tx_failed(t, lambda: t.s.tx(to=uniswap_multi.address, startgas=STARTGAS, value=2*ETH, sender=t.k2))
