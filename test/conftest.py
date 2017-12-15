import os
import pytest
from ethereum.tools import _solidity, tester
from ethereum.abi import ContractTranslator

OWN_DIR = os.path.dirname(os.path.realpath(__file__))

def get_dirs(path):
    abs_contract_path = os.path.realpath(os.path.join(OWN_DIR, '..', 'contracts'))
    sub_dirs = [x[0] for x in os.walk(abs_contract_path)]
    extra_args = ' '.join(['{}={}'.format(d.split('/')[-1], d) for d in sub_dirs])
    path = '{}/{}'.format(abs_contract_path, path)
    return path, extra_args

@pytest.fixture
def t():
    tester.s = tester.Chain({account: {'balance': 10**30}for account in tester.accounts})
    return tester

@pytest.fixture
def contract_tester(t):
    def create_contract(path, args=None, sender=t.k0):
        contract_name = path.split('/')[1]
        contract_name += ':' + contract_name.split('.')[0]
        path, extra_args = get_dirs(path)
        if args:
                args = [x.address if isinstance(x, t.ABIContract) else x for x in args]
        compiler = t.languages['solidity']
        combined = _solidity.compile_file(path, combined='bin,abi', optimize=True, extra_args=extra_args)
        abi = combined[contract_name]['abi']
        ct = ContractTranslator(abi)
        code = combined[contract_name]['bin'] + (ct.encode_constructor_arguments(args) if args else b'')
        address = t.s.tx(sender=sender, to=b'', value=0, data=code)
        return t.ABIContract(t.s, abi, address)
    return create_contract

@pytest.fixture
def assert_tx_failed():
    def assert_tx_failed(tester, function_to_test, exception = tester.TransactionFailed):
        initial_state = tester.s.snapshot()
        with pytest.raises(exception):
            function_to_test()
        tester.s.revert(initial_state)
    return assert_tx_failed
