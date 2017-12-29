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

Aproximate dev roadmap - some things will be worked on in parallel and the order could change

1) Smart Contract - add system for shared liquidity providers and fee payouts - COMPLETE

2) Python testing - IN PROGRESS

3) Smart Contract - Exchange Registry - IN PROGRESS

4) Frontend - begin work 

5) Switch liquidity shares to ERC20 tokens?

6) Finish setting up ENS

7) Smart Contract - Tunelling/Token-to-Token transfers

8) Testnet/formal audit

other stuff: social media/awareness push 