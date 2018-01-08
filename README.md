### Installation:

macOS Sierra

1) Install python 3 and upgrade pip (requies [Homebrew](https://brew.sh/))
```
$ xcode-select --install
$ brew install python3
$ pip3 install --upgrade pip
$ pip3 install virtualenv
```

2) Clone repository
```
$ git clone https://gitlab.com/haydena/automated-market-maker.git
$ cd automated-market-maker
```

3) Setup virtual environment (start in project folder)
```
$ virtualenv uniswap_environment
$ cd uniswap_environment
$ source bin/activate
$ cd ..
```

4) Install dependencies (in python environment)
```
$ pip3 install pytest
$ brew install pkg-config autoconf automake libyaml
$ env LDFLAGS="-L$(brew --prefix openssl)/lib" CFLAGS="-I$(brew --prefix openssl)/include" pip install scrypt
$ git clone https://github.com/ethereum/pyethereum/
$ cd pyethereum
$ python3 setup.py install
```

5) Run test
```
$ cd test/uniswap_exchange/
$ pytest
```


### Roadmap:

1) Basic ETH to ERC20 exchanges - COMPLETE

2) Decentralized liquidity providers with shared fee payouts - COMPLETE

3) Smart Contract - Exchange registry and factory - COMPLETE

4) ERC20 to ERC20 exchanges (tunneling between exchanges) - COMPLETE

5) Fine tuning and improvements to smart contracts - IN PROGRESS

6) Switch liquidity shares to ERC20 tokens? - NOT STARTED

7) Implement single token for all exchanges? - NOT STARTED

8) Python testing - IN PROGRESS (January, updated as smart contract changes)

9) ENS support - IN PROGRESS (test in January 2018, .eth domains expire every 2weeks on testnet)

10) Frontend - NOT STARTED (except for demo)

11) Testnet launch (Early/mid February)

12) Create bountry system or find alternative methods of funding (mid February)

13) Audit (Late February/March)

14) Mainet launch - April 2018?
