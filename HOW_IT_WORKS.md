# Uniswap Market Maker

[https://uniswap.io/](https://uniswap.io/)

Uniswap is an automated market maker exchange for ETH and ERC20 Tokens. It consists of a Factory/Registry contract which deploys an ETH-to-ERC20 exchange contract for any desired token. Exchanges are capable of "tunneling" between each other allowing direct ERC20-to-ERC20 purchases. Transaction fees within an exchange are split proportionally among liquidity providers who make the system possible. The basic mechanics of the exchange will be described in this document.

Code is simplified for clarity. Re-entrancy checks, transactions that timeout, and the ability to specify minimum tokens received are some of the safety features not shown in the code below.  

Uniswap is fully decentralized - anyone can contribute to the liquidity of a market and collect fees, or add a new exchange from the factory. There is no fee for the owner/dev.

# Exchange Creation
UniswapFactory.sol is a smart contract that serves as both a factory and registry for Uniswap exchanges. The public function `createExchange()` is show below:
```Solidity
import "./UniswapExchange.sol";

contract UniswapFactory(){
    mapping(address => address) tokenToExchange;
    mapping(address => address) exchangeToToken;

    function createExchange(address token) public returns (address exchange) {
        require(tokenToExchange[token] == address(0));  
        UniswapExchange newExchange = new UniswapExchange(token);
        tokenToExchange[token] = newExchange;
        exchangeToToken[newExchange] = token;
        return newExchange;
    }
}
```

Only one exchange can be launched per token. When a new token exchange is launched, a mapping between the token address and exchange address is created, adding it to the registry. The exchange associated with a token address can be found with the function:  

```Solidity
function tokenToExchangeLookup(address token) public view returns (address exchange) {
        return tokenToExchange[token];
    }
```

It is important to note that the factory does not perform any checks on the token address, other than to verify the token does not already have an associated exchange. It is recommended that users/frontends only interact with exchanges associated with known token addresses, such as [OmiseGo](https://etherscan.io/token/OmiseGo) or [Status](https://etherscan.io/token/StatusNetwork).

# ETH to ERC20 Exchange
The core ETH to Token exchange is based on [on_chain_market_maker.v.py](https://github.com/ethereum/vyper/blob/master/examples/market_maker/on_chain_market_maker.v.py).

### Example
An amount of both ETH and UNI (ERC20 Token) are deposited into a smart contract by liquidity providers. An invariant is set, such that ETH * UNI = Invariant. This invariant is held constant, except when liquidity is added or removed from the market.
> 10 ETH in market
> 100 UNI in market
> Invariant = 10 * 100 = 1000
>
If ETH is sent to the contract, the invariant is divided by the new amount of ETH in the market to get the new total UNI. The remaining UNI is sent to the buyer.
> Buyer sends 1 ETH
> 11 ETH in market
> 1000/11 = 90.9 UNI in market
> 100 - 90.9 = 9.1 UNI to buyer

The same process can be used for converting from UNI to ETH. A small fee is taken out for the liquidity providers, which will be described in greater detail further on.

# ERC20 to ERC20 Exchange
When an exchange is first created by the factory, the exchange is associated with a single token, and an interface for the factory is created:
```Solidity
/// CONSTRUCTOR
    function UniswapExchange(address _tokenAddress) public {
        tokenAddress = _tokenAddress;
        factoryAddress = msg.sender;
        token = ERC20Interface(tokenAddress);
        factory = FactoryInterface(factoryAddress);
    }
```
To convert from UNI to SWAP (two ERC20 tokens that totally exist), a buyer can call the function `tokenToTokenOut()` on the UNI exchange.
```Solidity
function tokenToTokenOut(address tokenAddress, uint256 tokensIn)
```
where `tokenAddress` is the address of SWAP token, and `tokensIn` is the UNI being sold.

This function first checks the registry to make sure the token has a registered exchange:
```
address exchangeAddress = factory.tokenToExchangeLookup(tokenAddress);
require(exchangeAddress != address(0) && exchangeAddress != address(this));
```
An instance of the other tokens exchange is created:
```Solidity
ExchangeInterface exchange = ExchangeInterface(exchangeAddress);
```

Next, the exchange converts from UNI to ETH as described in the previous section. However, instead of returning the purchased ETH to the buyer, the function instead calls the payable function `tokenToTokenIn()` on the SWAP exchange:
```Solidity
exchange.tokenToTokenIn.value(purchasedEth)(msg.sender)
```
tokenToTokenIn receives the ETH and buyer address, coverts the ETH to SWAP, and forwards the SWAP to the original buyer. Token-to-Token purchases have double the fees, since the fee must be paid on both exchanges.

# Invest / Divest
### Initialization
The first liquidity provider to invest in an exchange must initialize it. This is done by depositing an initial value of ETH and the exchange Token the contract, which sets the initial exchange rate. The provider is rewarded with initial "shares" of the market (based on the wei value deposited). These shares represent proportional ownership of the market and give the owner a proportional share of fee payouts.

### Investing
Once an exchange is initialized, investors can purchase shares by sending ETH and Tokens (at the current price ratio) using the `investLiquidity()` function:  
```Solidity
uint256 public ethInMarket;
uint256 public tokensInMarket;
uint256 public invariant;
uint256 public totalShares;
mapping(address => uint256) shares;

function investLiquidity() payable {
        uint256 ethPerShare = ethInMarket.div(totalShares);
        uint256 sharesPurchased = msg.value.div(ethPerShare);
        uint256 tokensPerShare = tokensInMarket.div(totalShares);
        uint256 tokensRequired = sharesPurchased.mul(tokensPerShare);
        shares[msg.sender] = shares[msg.sender].add(sharesPurchased);
        totalShares = totalShares.add(sharesPurchased);
        ethInMarket = ethInMarket.add(msg.value);
        tokensInMarket = tokensInMarket.add(tokensRequired);
        invariant = ethInMarket.mul(tokensInMarket);
        token.transferFrom(msg.sender, address(this), tokensRequired);
    }
```
The amount of shares purchased is determined by the amount of ETH sent to the function, and can be calulcated using the equation:

$sharesPurchased=\frac{ethSent*totalShares}{ethInMarket}$

The tokens required to purchase this amount of shares is calculated with:

$tokensRequired=\frac{sharesPurchased*tokensInMarket}{totalShares}$

If an investor has enought tokens, and has approved the exchange to call `transferFrom()` on the Tokens, then the investment will got through. If not, it will revert, and the ETH will be returned.

### Divesting
Investors can burn liquidity shares to withdraw a proportional share of ETH and Tokens from the market at any time.

$ethDivested=\frac{sharesBurned*ethInMarket}{totalShares}$

$tokensDivested=\frac{sharesBurned*tokensInMarket}{totalShares}$

ETH and Tokens are be withdrawn at the current market ratio, and not the ratio during the originial investment.

# Fee Structure
* For `ethToTokens()` there is a 0.2% fee paid in ETH
* For `tokensToETH()` there is a 0.2% fee paid in Tokens
* For `tokenToTokenOut()` there is a 0.2% fee paid in Tokens
* For `tokenToTokenIn()` there is a 0.2% fee paid in ETH

When a buyer swaps between currencies, they must pay a 0.1% fee to the liquidity providers on the exchange. Since ERC20-to-ERC20 purchases involve both an ERC20-to-ETH swap, and an ETH-to-ERC20 swap, the fee is paid on both exchanges.

As transactions occur on the exchanges, fees are temporarily stored in the variables `ethFees` and `tokenFees`. The function `addFeesToMarket()` adds these fees to the liquidity of the market, increasing the value of all market shares equally.

```
function addFeesToMarket() {
    ethInMarket = ethInMarket.add(ethFees);
    tokensInMarket = tokensInMarket.add(tokenFees);
    invariant = ethInMarket.mul(tokensInMarket);
    ethFees = 0;
    tokenFees = 0;
}
```
  This acts as a payout to liquidity providers, which is only collected when they burn shares. This means that exchange liquidity will grow at 0.1% of the transaction volume.`addFeesToMarket()` is called at the beginning of both `investLiquidity()` and `divestLiquidity()` which ensures that liquidity providers the exact amount of fees they are entitled to.
  
# Coming soon
### ENS
Convert ETH to UNI by sending ETH to uni.uniswap.eth
### Tradeable shares?
Could make shares ERC20 tokens that are tradeable. Potentially desirable, since shares appreciate in value, and represent a basket of ETH and a Token. Not sure if necessary.
### Finished Frontend
