### Installation:

macOS Sierra

1) Install python 3 and upgrade pip (requies [Homebrew](https://brew.sh/))
```
$ xcode-select --install
$ brew install python3
$ pip3 install --upgrade pip
$ pip3 install virtualenv
```

2) Clone repository (requies [Homebrew](https://brew.sh/))
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