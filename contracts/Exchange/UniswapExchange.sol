pragma solidity ^0.4.18;
import "./SafeMath.sol";
import "./ERC20Interface.sol";
import "./UniswapFactory.sol";


// Inteface for TokenToToken swaps across exchanges
contract ExchangeInterface {
    uint public FEE_RATE;
    uint256 public ethInMarket;
    uint256 public tokensInMarket;
    uint256 public invariant;
    uint256 public ethFeePool;
    uint256 public tokenFeePool;
    address public tokenAddress;
    ERC20Interface token;
    function ethToTokens(uint256 _minTokens, uint256 _timeout) external payable;
    function tokenToEth(uint256 _tokenAmount, uint256 _minEth, uint256 _timeout) external;
    function tokenToTokenOut(address buyTokenAddress, uint256 amount) external;
    function tokenToTokenIn(address buyer) public payable returns (bool);
    function tokenPurchase(address buyer, uint256 ethReceived, uint256 minTokens, uint256 timeout) internal;
    function ethPurchase(address buyer, uint256 tokenAmount, uint256 minEth, uint256 timeout) internal;
    event TokenPurchase(address indexed buyer, uint256 tokensPurchased, uint256 ethSpent);
    event EthPurchase(address indexed buyer, uint256 ethPurchased, uint256 tokensSpent);
}


contract UniswapExchange {
    using SafeMath for uint256;

    event TokenPurchase(address indexed buyer, uint256 tokensPurchased, uint256 ethSpent);
    event EthPurchase(address indexed buyer, uint256 ethPurchased, uint256 tokensSpent);
    event Investment(address indexed liquidityProvider, uint256 indexed sharesPurchased);
    event Divestment(address indexed liquidityProvider, uint256 indexed sharesSold);

    /// CONSTANTS
    uint256 public constant FEE_RATE = 500;        //fee = 1/feeRate = 0.2%

    /// STORAGE
    uint256 public ethInMarket;
    uint256 public tokensInMarket;
    uint256 public invariant;
    uint256 public ethFeePool;
    uint256 public tokenFeePool;
    uint256 public totalShares;
    uint256 public lastFeeDistribution;
    address public tokenAddress;
    address public factoryAddress;
    mapping(address => uint256) liquidityShares;
    mapping(address => uint256) divestedEthBalance;
    mapping(address => uint256) divestedTokenBalance;
    mapping(address => uint256) feeBalance;
    ERC20Interface token;
    FactoryInterface factory;

    modifier waitingPeriod() {
        uint lockoutEnd = lastFeeDistribution.add(1 weeks);
        require(now > lockoutEnd);
        _;
    }

    modifier onlyExchange() {
        require(factory.isAddressAnExchange(msg.sender));
        _;
    }

    modifier exchangeInitialized() {
        require(invariant > 0 && totalShares > 0);
        _;
    }

    /// CONSTRUCTOR
    function UniswapExchange(address _tokenAddress) public {
        tokenAddress = _tokenAddress;
        token = ERC20Interface(tokenAddress);
        factoryAddress = msg.sender;
        factory = FactoryInterface(factoryAddress);
        tokenAddress = _tokenAddress;
        token = ERC20Interface(tokenAddress);
        lastFeeDistribution = now;
    }

    /// FALLBACK FUNCTION
    function() public payable {
        require(msg.value != 0);
        uint256 _timeout = now.add(300);
        tokenPurchase(msg.sender, msg.value, 1, _timeout);
    }

    /// EXTERNAL FUNCTIONS
    function initializeExchange(uint256 tokenAmount) external payable {
        require(invariant == 0 && totalShares == 0);
        // Prevents share cost from being too high or too low - potentially needs work
        require(msg.value >= 10000 && tokenAmount >= 10000 && msg.value <= 5*10**18);
        ethInMarket = msg.value;
        tokensInMarket = tokenAmount;
        invariant = ethInMarket.mul(tokensInMarket);
        liquidityShares[msg.sender] = 1000;
        totalShares = 1000;
        require(token.transferFrom(msg.sender, address(this), tokenAmount));
    }

    function ethToTokens(uint256 _minTokens, uint256 _timeout) external payable {
        require(msg.value > 0 && _minTokens > 0);
        tokenPurchase(msg.sender, msg.value,  _minTokens, _timeout);
    }

    function tokenToEth(uint256 _tokenAmount, uint256 _minEth, uint256 _timeout) external {
        require(_tokenAmount != 0 && _minEth != 0);
        ethPurchase(msg.sender, _tokenAmount, _minEth, _timeout);
    }

    // Swaps TOKEN1 for ETH on current exchange, calls ETH to TOKEN2 on second exchange
    function tokenToTokenOut(address buyTokenAddress, uint256 amount) external exchangeInitialized {
        require(amount != 0);
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
        require(token.transferFrom(msg.sender, address(this), amount));
        require(exchange.tokenToTokenIn.value(purchasedEth)(msg.sender));
    }

    function tokenToTokenIn(address buyer) external payable returns (bool) {
        require(msg.value != 0);
        uint256 _timeout = now.add(300);
        tokenPurchase(buyer, msg.value, 1, _timeout);
        return true;
    }

    //edge case - market movement?
    function investLiquidity() external payable exchangeInitialized {
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
        require(token.transferFrom(msg.sender, address(this), tokensRequired));
    }

    function divestLiquidity(uint256 sharesSold) external {
        require(liquidityShares[msg.sender] >= sharesSold && sharesSold > 0);
        liquidityShares[msg.sender] = liquidityShares[msg.sender].sub(sharesSold);
        uint256 weiPerShare = ethInMarket.div(totalShares);
        uint256 tokensPerShare = tokensInMarket.div(totalShares);
        uint256 weiDivested = weiPerShare.mul(sharesSold);
        uint256 tokensDivested = tokensPerShare.mul(sharesSold);
        totalShares = totalShares.sub(sharesSold);
        ethInMarket = ethInMarket.sub(weiDivested);
        tokensInMarket = tokensInMarket.sub(tokensDivested);
        if (sharesSold == totalShares) {
            invariant == 0;
        } else {
            invariant = ethInMarket.mul(tokensInMarket);
        }
        Divestment(msg.sender, sharesSold);
        require(token.transfer(msg.sender, tokensDivested));
        msg.sender.transfer(weiDivested);
    }

    function getShares(address provider) external view returns(uint256 shares) {
        return liquidityShares[provider];
    }

    /// PUBLIC FUNCTIONS
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

    /// INTERNAL FUNCTIONS
    function tokenPurchase(address buyer, uint256 ethReceived, uint256 minTokens, uint256 timeout) internal exchangeInitialized {
        require(now < timeout);
        uint256 fee = ethReceived.div(FEE_RATE);
        uint256 ethSold = ethReceived.sub(fee);
        uint256 newEthInMarket = ethInMarket.add(ethSold);
        uint256 newTokensInMarket = invariant.div(newEthInMarket);
        uint256 purchasedTokens = tokensInMarket.sub(newTokensInMarket);
        require(purchasedTokens >= minTokens && purchasedTokens <= tokensInMarket);
        ethFeePool = ethFeePool.add(fee);
        ethInMarket = newEthInMarket;
        tokensInMarket = newTokensInMarket;
        TokenPurchase(buyer, purchasedTokens, ethSold);
        require(token.transfer(buyer, purchasedTokens));
    }

    function ethPurchase(address buyer, uint256 tokenAmount, uint256 minEth, uint256 timeout) internal exchangeInitialized {
        require(now < timeout);
        uint256 fee = tokenAmount.div(FEE_RATE);
        uint256 tokensSold = tokenAmount.sub(fee);
        uint256 newTokensInMarket = tokensInMarket.add(tokensSold);
        uint256 newEthInMarket = invariant.div(newTokensInMarket);
        uint256 purchasedEth = ethInMarket.sub(newEthInMarket);
        require(purchasedEth >= minEth && purchasedEth <= ethInMarket);
        tokenFeePool = tokenFeePool.add(fee);
        tokensInMarket = newTokensInMarket;
        ethInMarket = newEthInMarket;
        EthPurchase(buyer, purchasedEth, tokensSold);
        require(token.transferFrom(buyer, address(this), tokenAmount));
        buyer.transfer(purchasedEth);
    }
}
