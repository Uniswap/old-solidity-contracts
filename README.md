## Installation:

#### Tested in macOS High Sierra

1) Install python 3 and upgrade pip (requies [Homebrew](https://brew.sh/))
```
$ xcode-select --install (if needed)
$ brew install python3
$ brew install pkg-config autoconf automake libyaml
```

2) Clone repository
```
$ git clone https://github.com/Uniswap/contracts.git
$ cd contracts
```

3) Setup virtual environment (recommended)
```
$ pip3 install --upgrade pip
$ pip3 install virtualenv
$ virtualenv uniswap_environment
$ source uniswap_environment/bin/activate
```

4) Install dependencies (in python environment)
```
$ env LDFLAGS="-L$(brew --prefix openssl)/lib" CFLAGS="-I$(brew --prefix openssl)/include" pip3 install scrypt
$ python3 setup.py install
```

5) Run tests
```
$ cd test
$ pytest -v
```


## Roadmap:

1) Basic ETH to ERC20 exchanges - COMPLETE

2) Decentralized liquidity providers with shared fee payouts - COMPLETE

3) Exchange registry and factory - COMPLETE

4) ERC20 to ERC20 exchanges (tunneling between exchanges) - COMPLETE

5) Anything to anything payments (similar to ShapeShift) - COMPLETE

6) Python testing - IN PROGRESS

7) Switch liquidity shares to ERC20 tokens? - (might not implement)

8) Implement single token for all exchanges? - (might not implement)

9) Fine tuning and improvements to smart contracts - IN PROGRESS

10) Frontend - IN PROGRESS

11) ENS support - IN PROGRESS

12) Testnet launch (Early/mid February)

13) Mainet Bounties

14) Audit (Late February/March)

15) Mainet launch - April 2018?
