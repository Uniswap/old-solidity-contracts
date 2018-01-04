pragma solidity ^0.4.18;
import "./UniswapLiquidityProviders.sol";
/* import "./UniswapFactoryTokenToToken.sol"; */

/// NEEDS WORK

contract ExchangeInterface {
    uint public FEE_RATE;
    uint256 public ethInMarket;
    uint256 public tokensInMarket;
    uint256 public invariant;
    uint256 public ethFeePool;
    uint256 public tokenFeePool;
    address public tokenAddress;
    ERC20Token token;
    function ethToTokens(uint256 minTokens, uint256 timeout) public payable;
    function fallbackEthToTokens(address buyer, uint256 value, uint256 timeout) public payable;
    function tokenToEth(uint256 tokenAmount, uint256 minEth, uint256 timeout) public;
    function tokenToEthToTunnel(address buyTokenAddress, uint256 amount) public;
    function tunnelToEthToToken(address buyer) public payable;
    event TokenPurchase(address indexed buyer, uint256 tokensPurchased, uint256 ethSpent);
    event EthPurchase(address indexed buyer, uint256 ethPurchased, uint256 tokensSpent);
}


contract UniswapTokenToToken is UniswapLiquidityProviders {

    // Address of token registry
    address public factoryAddress;
    /* FactoryInterface factory; */

    function UniswapTokenToToken(address _tokenAddress) public
        UniswapLiquidityProviders(_tokenAddress)
    {
        factoryAddress = msg.sender;
        /* factory = FactoryInterface(factoryAddress); */

        tokenAddress = _tokenAddress;
        token = ERC20Token(tokenAddress);
        lastFeeDistribution = now;
    }


    /// too much gas
    function tokenToEthToTunnel(address exchangeAddress, uint256 amount) public {
        require(invariant > 0 && amount !=0);
        /* address exchangeAddress = factory.tokenExchangeLookup(buyTokenAddress); */
        require(exchangeAddress != address(0) && exchangeAddress != address(this));
        uint256 fee = amount.div(FEE_RATE);
        uint256 tokensSold = amount.sub(fee);
        uint256 newTokensInMarket = tokensInMarket.add(tokensSold);
        uint256 newEthInMarket = invariant.div(newTokensInMarket);
        uint256 purchasedEth = ethInMarket.sub(newEthInMarket);
        require(purchasedEth <= ethInMarket);
        ExchangeInterface exchange = ExchangeInterface(exchangeAddress);
        EthPurchase(msg.sender, purchasedEth, tokensSold);
        tokenFeePool = tokenFeePool.add(fee);
        tokensInMarket = newTokensInMarket;
        ethInMarket = newEthInMarket;
        token.transferFrom(msg.sender, address(this), amount);
        exchange.tunnelToEthToToken.value(purchasedEth)(msg.sender);
    }


    function tunnelToEthToToken(address buyer) public payable {
        require(invariant > 0);
        uint256 fee = msg.value.div(FEE_RATE);
        uint256 ethSold = msg.value.sub(fee);
        uint256 newEthInMarket = ethInMarket.add(ethSold);
        uint256 newTokensInMarket = invariant.div(newEthInMarket);
        uint256 purchasedTokens = tokensInMarket.sub(newTokensInMarket);
        //require(purchasedTokens <= tokensInMarket.div(10)); //cannot buy more than 10% of tokens through fallback function
        ethFeePool = ethFeePool.add(fee);
        ethInMarket = newEthInMarket;
        tokensInMarket = newTokensInMarket;
        TokenPurchase(buyer, purchasedTokens, ethSold);
        token.transfer(buyer, purchasedTokens);
    }

}
