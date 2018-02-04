pragma solidity ^0.4.18;
import "./SafeMath.sol";
import "./ERC20Interface.sol";
import "./UniswapFactory.sol";


// Inteface for TokenToToken swaps across exchanges - does not have all methods
contract ExchangeInterface {
    uint public FEE_RATE;
    uint256 public ethInMarket;
    uint256 public tokensInMarket;
    uint256 public invariant;
    uint256 public ethFees;
    uint256 public tokenFees;
    address public tokenAddress;
    mapping(address => uint256) shares;
    ERC20Interface token;
    function ethToTokenSwap(uint256 _minTokens, uint256 _timeout) external payable;
    function ethToTokenPayment(uint256 _minTokens, uint256 _timeout, address _beneficiary) external payable;
    function tokenToEthSwap(uint256 _tokenAmount, uint256 _minEth, uint256 _timeout) external;
    function tokenToEthPayment(uint256 _tokenAmount, uint256 _minEth, uint256 _timeout, address _beneficiary) external;
    function tokenToTokenSwap(address _buyTokenAddress, uint256 _tokensSold, uint256 _minTokensReceived, uint256 _timeout) external;
    function tokenToTokenPayment(address _buyTokenAddress, address _beneficiary, uint256 _tokensSold, uint256 _minTokensReceived, uint256 _timeout) external;
    function tokenToTokenIn(address buyer, uint256 _minTokens) external payable returns (bool);
    function ethToToken(address buyer, address recipient, uint256 ethIn, uint256 minTokensOut) internal;
    function tokenToEth(address buyer, address recipient, uint256 tokensIn, uint256 minEthOut) internal;
    function tokenToTokenOut(address buyTokenAddress, address buyer, address recipient, uint256 tokensIn, uint256 minTokensOut) internal;
    event TokenPurchase(address indexed buyer, uint256 tokensPurchased, uint256 ethSpent);
    event EthPurchase(address indexed buyer, uint256 ethPurchased, uint256 tokensSpent);
}


contract UniswapExchange {
    using SafeMath for uint256;

    /// EVENTS
    event TokenPurchase(address indexed buyer, uint256 tokensPurchased, uint256 ethSpent);
    event EthPurchase(address indexed buyer, uint256 ethPurchased, uint256 tokensSpent);
    event Investment(address indexed liquidityProvider, uint256 indexed sharesPurchased);
    event Divestment(address indexed liquidityProvider, uint256 indexed sharesBurned);

    /// CONSTANTS
    uint256 public constant FEE_RATE = 500;        //fee = 1/feeRate = 0.2%

    /// STORAGE
    uint256 public ethInMarket;
    uint256 public tokensInMarket;
    uint256 public invariant;
    uint256 public ethFees;
    uint256 public tokenFees;
    uint256 public totalShares;
    address public tokenAddress;
    address public factoryAddress;
    mapping(address => uint256) shares;
    ERC20Interface token;
    FactoryInterface factory;

    /// MODIFIERS
    modifier exchangeInitialized() {
        require(invariant > 0 && totalShares > 0);
        _;
    }

    /// CONSTRUCTOR
    function UniswapExchange(address _tokenAddress) public {
        tokenAddress = _tokenAddress;
        factoryAddress = msg.sender;
        token = ERC20Interface(tokenAddress);
        factory = FactoryInterface(factoryAddress);
    }

    /// FALLBACK FUNCTION
    function() public payable {
        require(msg.value != 0);
        ethToToken(msg.sender, msg.sender, msg.value, 1);
    }

    /// EXTERNAL FUNCTIONS
    function initializeExchange(uint256 tokenAmount) external payable {
        require(invariant == 0 && totalShares == 0);
        // Prevents share cost from being too high or too low - potentially needs work
        require(msg.value >= 10000 && tokenAmount >= 10000 && msg.value <= 5*10**18);
        ethInMarket = msg.value;
        tokensInMarket = tokenAmount;
        invariant = ethInMarket.mul(tokensInMarket);
        shares[msg.sender] = 1000;
        totalShares = 1000;
        require(token.transferFrom(msg.sender, address(this), tokenAmount));
    }

    // Buyer swaps ETH for Tokens
    function ethToTokenSwap(uint256 _minTokens, uint256 _timeout) external payable {
        require(msg.value > 0 && _minTokens > 0 && now < _timeout);
        ethToToken(msg.sender, msg.sender, msg.value,  _minTokens);
    }

    // Payer pays in ETH, beneficiary receives Tokens
    function ethToTokenPayment(uint256 _minTokens, uint256 _timeout, address _beneficiary) external payable {
        require(msg.value > 0 && _minTokens > 0 && now < _timeout);
        require(_beneficiary != address(0) && _beneficiary != address(this));
        ethToToken(msg.sender, _beneficiary, msg.value,  _minTokens);
    }

    // Buyer swaps Tokens for ETH
    function tokenToEthSwap(uint256 _tokenAmount, uint256 _minEth, uint256 _timeout) external {
        require(_tokenAmount > 0 && _minEth > 0 && now < _timeout);
        tokenToEth(msg.sender, msg.sender, _tokenAmount, _minEth);
    }

    // Payer pays in Tokens, beneficiary receives ETH
    function tokenToEthPayment(
        uint256 _tokenAmount,
        uint256 _minEth,
        uint256 _timeout,
        address _beneficiary
    )
        external
    {
        require(_tokenAmount > 0 && _minEth > 0 && now < _timeout);
        require(_beneficiary != address(0) && _beneficiary != address(this));
        tokenToEth(msg.sender, _beneficiary, _tokenAmount, _minEth);
    }

    // Buyer swaps Tokens in current exchange for Tokens of provided address
    function tokenToTokenSwap(
        address _buyTokenAddress,     // Must be a token with an attached Uniswap exchange
        uint256 _tokensSold,
        uint256 _minTokensReceived,
        uint256 _timeout
    )
        external
    {
        require(_tokensSold > 0 && _minTokensReceived > 0 && now < _timeout);
        tokenToTokenOut(_buyTokenAddress, msg.sender, msg.sender, _tokensSold, _minTokensReceived);
    }

    // Payer pays in exchange Token, beneficiary receives Tokens of provided address
    function tokenToTokenPayment(
        address _buyTokenAddress,
        address _beneficiary,
        uint256 _tokensSold,
        uint256 _minTokensReceived,
        uint256 _timeout
    )
        external
    {
        require(_tokensSold > 0 && _minTokensReceived > 0 && now < _timeout);
        require(_beneficiary != address(0) && _beneficiary != address(this));
        tokenToTokenOut(_buyTokenAddress, msg.sender, _beneficiary, _tokensSold, _minTokensReceived);
    }

    // Function called by another Uniswap exchange in Token to Token swaps and payments
    function tokenToTokenIn(address recipient, uint256 _minTokens) external payable returns (bool) {
        require(msg.value > 0);
        address exchangeToken = factory.exchangeToTokenLookup(msg.sender);
        require(exchangeToken != address(0));   // Only a Uniswap exchange can call this function
        ethToToken(msg.sender, recipient, msg.value, _minTokens);
        return true;
    }

    // Invest liquidity and receive market shares
    function investLiquidity(uint256 minShares) external payable exchangeInitialized {
        require(msg.value > 0 && minShares > 0);
        addFeesToMarket();
        uint256 ethPerShare = ethInMarket.div(totalShares);
        require(msg.value >= ethPerShare);
        uint256 sharesPurchased = msg.value.div(ethPerShare);
        require(sharesPurchased >= minShares);
        uint256 tokensPerShare = tokensInMarket.div(totalShares);
        uint256 tokensRequired = sharesPurchased.mul(tokensPerShare);
        shares[msg.sender] = shares[msg.sender].add(sharesPurchased);
        totalShares = totalShares.add(sharesPurchased);
        ethInMarket = ethInMarket.add(msg.value);
        tokensInMarket = tokensInMarket.add(tokensRequired);
        invariant = ethInMarket.mul(tokensInMarket);
        Investment(msg.sender, sharesPurchased);
        require(token.transferFrom(msg.sender, address(this), tokensRequired));
    }

    // Divest market shares and receive liquidity
    function divestLiquidity(uint256 sharesBurned, uint256 minEth, uint256 minTokens) external {
        require(sharesBurned > 0);
        shares[msg.sender] = shares[msg.sender].sub(sharesBurned);
        addFeesToMarket();
        uint256 ethPerShare = ethInMarket.div(totalShares);
        uint256 tokensPerShare = tokensInMarket.div(totalShares);
        uint256 ethDivested = ethPerShare.mul(sharesBurned);
        uint256 tokensDivested = tokensPerShare.mul(sharesBurned);
        require(ethDivested >= minEth && tokensDivested >= minTokens);
        totalShares = totalShares.sub(sharesBurned);
        ethInMarket = ethInMarket.sub(ethDivested);
        tokensInMarket = tokensInMarket.sub(tokensDivested);
        if (totalShares == 0) {
            invariant = 0;
        } else {
            invariant = ethInMarket.mul(tokensInMarket);
        }
        Divestment(msg.sender, sharesBurned);
        require(token.transfer(msg.sender, tokensDivested));
        msg.sender.transfer(ethDivested);
    }

    // View share balance of an address
    function getShares(address provider) external view returns(uint256 _shares) {
        return shares[provider];
    }

    /// PUBLIC FUNCTIONS
    // Add fees to market, increasing value of all shares
    function addFeesToMarketPublic() public {
        require(ethFees != 0 || tokenFees != 0);
        addFeesToMarket();
    }

    /// INTERNAL FUNCTIONS
    function ethToToken(
        address buyer,
        address recipient,
        uint256 ethIn,
        uint256 minTokensOut
    )
        internal
        exchangeInitialized
    {
        uint256 fee = ethIn.div(FEE_RATE);
        uint256 ethSold = ethIn.sub(fee);
        uint256 newEthInMarket = ethInMarket.add(ethSold);
        uint256 newTokensInMarket = invariant.div(newEthInMarket);
        uint256 tokensOut = tokensInMarket.sub(newTokensInMarket);
        require(tokensOut >= minTokensOut && tokensOut <= tokensInMarket);
        ethFees = ethFees.add(fee);
        ethInMarket = newEthInMarket;
        tokensInMarket = newTokensInMarket;
        TokenPurchase(buyer, tokensOut, ethSold);
        require(token.transfer(recipient, tokensOut));
    }

    function tokenToEth(
        address buyer,
        address recipient,
        uint256 tokensIn,
        uint256 minEthOut
    )
        internal
        exchangeInitialized
    {
        uint256 fee = tokensIn.div(FEE_RATE);
        uint256 tokensSold = tokensIn.sub(fee);
        uint256 newTokensInMarket = tokensInMarket.add(tokensSold);
        uint256 newEthInMarket = invariant.div(newTokensInMarket);
        uint256 ethOut = ethInMarket.sub(newEthInMarket);
        require(ethOut >= minEthOut && ethOut <= ethInMarket);
        tokenFees = tokenFees.add(fee);
        tokensInMarket = newTokensInMarket;
        ethInMarket = newEthInMarket;
        EthPurchase(buyer, ethOut, tokensIn);
        require(token.transferFrom(buyer, address(this), tokensIn));
        recipient.transfer(ethOut);
    }

    function tokenToTokenOut(
        address buyTokenAddress,
        address buyer,
        address recipient,
        uint256 tokensIn,
        uint256 minTokensOut
    )
        internal
        exchangeInitialized
    {
        require(buyTokenAddress != address(0) && buyTokenAddress != address(this));
        address exchangeAddress = factory.tokenToExchangeLookup(buyTokenAddress);
        require(exchangeAddress != address(0) && exchangeAddress != address(this));
        uint256 fee = tokensIn.div(FEE_RATE);
        uint256 tokensSold = tokensIn.sub(fee);
        uint256 newTokensInMarket = tokensInMarket.add(tokensSold);
        uint256 newEthInMarket = invariant.div(newTokensInMarket);
        uint256 ethOut = ethInMarket.sub(newEthInMarket);
        require(ethOut <= ethInMarket);
        ExchangeInterface exchange = ExchangeInterface(exchangeAddress);
        EthPurchase(buyer, ethOut, tokensSold);
        tokenFees = tokenFees.add(fee);
        tokensInMarket = newTokensInMarket;
        ethInMarket = newEthInMarket;
        require(token.transferFrom(buyer, address(this), tokensIn));
        require(exchange.tokenToTokenIn.value(ethOut)(recipient, minTokensOut));
    }

    function addFeesToMarket() internal {
        if (ethFees > 0 || tokenFees > 0) {
            uint256 newEth = ethFees;
            uint256 newTokens = tokenFees;
            ethFees = 0;
            tokenFees = 0;
            ethInMarket = ethInMarket.add(newEth);
            tokensInMarket = tokensInMarket.add(newTokens);
            invariant = ethInMarket.mul(tokensInMarket);
        }
    }
}
