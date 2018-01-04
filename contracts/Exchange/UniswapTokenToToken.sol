pragma solidity ^0.4.18;
import "./SafeMath.sol";
import "./ERC20Interface.sol";
import "./UniswapFactory.sol";


contract ExchangeInterface {
    uint public FEE_RATE;
    uint256 public ethInMarket;
    uint256 public tokensInMarket;
    uint256 public invariant;
    uint256 public ethFeePool;
    uint256 public tokenFeePool;
    address public tokenAddress;
    ERC20Interface token;
    function ethToTokens(uint256 minTokens, uint256 timeout) public payable;
    function fallbackEthToTokens(address buyer, uint256 value, uint256 timeout) public payable;
    function tokenToEth(uint256 tokenAmount, uint256 minEth, uint256 timeout) public;
    function tokenToEthToTunnel(address buyTokenAddress, uint256 amount) public;
    function tunnelToEthToToken(address buyer) public payable;
    event TokenPurchase(address indexed buyer, uint256 tokensPurchased, uint256 ethSpent);
    event EthPurchase(address indexed buyer, uint256 ethPurchased, uint256 tokensSpent);
}


contract UniswapBasic {
    using SafeMath for uint256;

    event TokenPurchase(address indexed buyer, uint256 tokensPurchased, uint256 ethSpent);
    event EthPurchase(address indexed buyer, uint256 ethPurchased, uint256 tokensSpent);

    uint public constant FEE_RATE = 500;        //fee = 1/feeRate = 0.2%

    uint256 public ethInMarket;
    uint256 public tokensInMarket;
    uint256 public invariant;
    uint256 public ethFeePool;
    uint256 public tokenFeePool;
    address public tokenAddress;
    ERC20Interface token;

    function UniswapBasic(address _tokenAddress) public {
        tokenAddress = _tokenAddress;
        token = ERC20Interface(tokenAddress);
    }

    function() public payable {
        require(msg.value != 0);
        uint256 time = now + 300;
        fallbackEthToTokens(msg.sender, msg.value, time);
    }

    function ethToTokens(uint256 minTokens, uint256 timeout) public payable {
        require(invariant > 0);
        require(msg.value != 0 && minTokens != 0 && now < timeout);
        uint256 fee = msg.value.div(FEE_RATE);
        uint256 ethSold = msg.value.sub(fee);
        uint256 newEthInMarket = ethInMarket.add(ethSold);
        uint256 newTokensInMarket = invariant.div(newEthInMarket);
        uint256 purchasedTokens = tokensInMarket.sub(newTokensInMarket);
        require(purchasedTokens >= minTokens && purchasedTokens <= tokensInMarket);
        ethFeePool = ethFeePool.add(fee);
        ethInMarket = newEthInMarket;
        tokensInMarket = newTokensInMarket;
        TokenPurchase(msg.sender, purchasedTokens, ethSold);
        token.transfer(msg.sender, purchasedTokens);
    }

    function fallbackEthToTokens(address buyer, uint256 value, uint256 timeout) public payable {
        require(invariant > 0);
        require(value != 0 && now < timeout);
        uint256 fee = value.div(FEE_RATE);
        uint256 ethSold = value.sub(fee);
        uint256 newEthInMarket = ethInMarket.add(ethSold);
        uint256 newTokensInMarket = invariant.div(newEthInMarket);
        uint256 purchasedTokens = tokensInMarket.sub(newTokensInMarket);
        uint256 maxTokens = tokensInMarket.div(5); // Can't purchase more than 20% of tokens using fallback
        require(purchasedTokens > 0 && purchasedTokens <= maxTokens);
        ethFeePool = ethFeePool.add(fee);
        ethInMarket = newEthInMarket;
        tokensInMarket = newTokensInMarket;
        TokenPurchase(buyer, purchasedTokens, ethSold);
        token.transfer(buyer, purchasedTokens);
    }

    function tokenToEth(uint256 tokenAmount, uint256 minEth, uint256 timeout) public {
        require(invariant > 0);
        require(tokenAmount != 0 && minEth != 0 && now < timeout);
        uint256 fee = tokenAmount.div(FEE_RATE);
        uint256 tokensSold = tokenAmount.sub(fee);
        uint256 newTokensInMarket = tokensInMarket.add(tokensSold);
        uint256 newEthInMarket = invariant.div(newTokensInMarket);
        uint256 purchasedEth = ethInMarket.sub(newEthInMarket);
        require(purchasedEth >= minEth && purchasedEth <= ethInMarket);
        tokenFeePool = tokenFeePool.add(fee);
        tokensInMarket = newTokensInMarket;
        ethInMarket = newEthInMarket;
        EthPurchase(msg.sender, purchasedEth, tokensSold);
        msg.sender.transfer(purchasedEth);
        token.transferFrom(msg.sender, address(this), tokenAmount);
    }
}


contract UniswapLiquidityProviders is UniswapBasic {
    using SafeMath for uint256;

    event Investment(address indexed liquidityProvider, uint256 indexed sharesPurchased);
    event Divestment(address indexed liquidityProvider, uint256 indexed sharesSold);

    uint256 public totalShares;
    uint256 public lastFeeDistribution;
    mapping(address => uint256) liquidityShares;
    mapping(address => uint256) divestedEthBalance;
    mapping(address => uint256) divestedTokenBalance;
    mapping(address => uint256) feeBalance;

    modifier waitingPeriod() {
        uint lockoutEnd = lastFeeDistribution.add(1 weeks);
        require(now > lockoutEnd);
        _;
    }

    function UniswapLiquidityProviders(address _tokenAddress) public
        UniswapBasic(_tokenAddress)
    {
        lastFeeDistribution = now;
    }

    // Needs work - numbers are somewhat arbitrary right now
    function initializeExchange(uint256 tokenAmount) external payable {
        require(invariant == 0 && totalShares == 0);
        // Prevents share cost from being too high or too low - potentially needs work
        require(msg.value >= 10000 && tokenAmount >= 10000 && msg.value <= 5*10**18);
        ethInMarket = msg.value;
        tokensInMarket = tokenAmount;
        invariant = ethInMarket.mul(tokensInMarket);
        liquidityShares[msg.sender] = 1000;
        totalShares = 1000;
        token.transferFrom(msg.sender, address(this), tokenAmount);
    }

    function investLiquidity() external payable {
        require(invariant != 0);
        uint256 weiPerShare = ethInMarket.div(totalShares);
        require(msg.value >= weiPerShare);
        uint256 sharesPurchased = msg.value.div(weiPerShare);
        uint256 tokensPerShare = tokensInMarket.div(totalShares);
        uint256 tokensRequired = sharesPurchased.mul(tokensPerShare);
        liquidityShares[msg.sender] = liquidityShares[msg.sender].add(sharesPurchased);
        totalShares = totalShares.add(sharesPurchased);
        ethInMarket = ethInMarket.add(msg.value);
        tokensInMarket = tokensInMarket.add(tokensRequired);
        invariant = ethInMarket.mul(tokensInMarket);
        Investment(msg.sender, sharesPurchased);
        token.transferFrom(msg.sender, address(this), tokensRequired);
    }

    function divestLiquidity(uint256 sharesSold) external {
        require(liquidityShares[msg.sender] >= sharesSold && sharesSold > 0);
        liquidityShares[msg.sender] = liquidityShares[msg.sender].sub(sharesSold);
        uint256 weiPerShare = ethInMarket.div(totalShares);
        uint256 tokensPerShare = tokensInMarket.div(totalShares);
        uint256 weiDivested = weiPerShare.mul(sharesSold);
        uint256 tokensDivested = tokensPerShare.mul(sharesSold);
        totalShares = totalShares.sub(sharesSold);
        divestedEthBalance[msg.sender] = divestedEthBalance[msg.sender].add(weiDivested);
        divestedTokenBalance[msg.sender] = divestedEthBalance[msg.sender].add(tokensDivested);
        ethInMarket = ethInMarket.sub(weiDivested);
        tokensInMarket = tokensInMarket.sub(tokensDivested);
        if (sharesSold == totalShares) {
            invariant == 0;
        } else {
            invariant = ethInMarket.mul(tokensInMarket);
        }
        Divestment(msg.sender, sharesSold);
    }

    function withdrawDivestedEth() external {
        require(divestedEthBalance[msg.sender] != 0);
        uint256 divestedEth = divestedEthBalance[msg.sender];
        divestedEthBalance[msg.sender] = 0;
        msg.sender.transfer(divestedEth);
    }

    function withdrawDivestedTokens() external {
        require(divestedTokenBalance[msg.sender] != 0);
        uint256 divestedTokens = divestedTokenBalance[msg.sender];
        divestedTokenBalance[msg.sender] = 0;
        token.transfer(msg.sender, divestedTokens);
    }

    function getShares(address provider) external view returns(uint256 shares) {
        return liquidityShares[provider];
    }

    function getDivestedBalances(address provider) external view returns(uint256 ethBal, uint256 tokBal) {
        ethBal = divestedEthBalance[provider];
        tokBal = divestedTokenBalance[provider];
    }

    // Add fees to market, increasing value of all shares
    function addFeesToMarket() public waitingPeriod {
        require(ethFeePool != 0 || tokenFeePool != 0);
        uint256 ethFees = ethFeePool;
        uint256 tokenFees = tokenFeePool;
        ethFeePool = 0;
        tokenFeePool = 0;
        lastFeeDistribution = now;
        ethInMarket = ethInMarket.add(ethFees);
        tokensInMarket = tokensInMarket.add(tokenFees);
        invariant = ethInMarket.mul(tokensInMarket);
    }
}


contract UniswapTokenToToken is UniswapLiquidityProviders {

    // Address of token registry
    address public factoryAddress;
    FactoryInterface factory;

    modifier onlyExchange() {
        require(factory.isAddressAnExchange(msg.sender));
        _;
    }

    function UniswapTokenToToken(address _tokenAddress) public
        UniswapLiquidityProviders(_tokenAddress)
    {
        factoryAddress = msg.sender;
        factory = FactoryInterface(factoryAddress);

        tokenAddress = _tokenAddress;
        token = ERC20Interface(tokenAddress);
        lastFeeDistribution = now;
    }

    function tokenToEthToTunnel(address buyTokenAddress, uint256 amount) public {
        require(invariant > 0 && amount != 0);
        address exchangeAddress = factory.tokenToExchangeLookup(buyTokenAddress);
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
