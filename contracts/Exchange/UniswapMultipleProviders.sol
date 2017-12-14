pragma solidity ^0.4.18;


library SafeMath {
  function mul(uint256 a, uint256 b) internal pure returns (uint256) {
    if (a == 0) {
      return 0;
    }
    uint256 c = a * b;
    assert(c / a == b);
    return c;
  }

  function div(uint256 a, uint256 b) internal pure returns (uint256) {
    // assert(b > 0); // Solidity automatically throws when dividing by 0
    uint256 c = a / b;
    // assert(a == b * c + a % b); // There is no case in which this doesn't hold
    return c;
  }

  function sub(uint256 a, uint256 b) internal pure returns (uint256) {
    assert(b <= a);
    return a - b;
  }

  function add(uint256 a, uint256 b) internal pure returns (uint256) {
    uint256 c = a + b;
    assert(c >= a);
    return c;
  }
}


contract ERC20Token {
    uint256 public totalSupply;
    function balanceOf(address who) public constant returns (uint256);
    function transfer(address to, uint256 value) public returns (bool);
    function allowance(address owner, address spender) public constant returns (uint256);
    function transferFrom(address from, address to, uint256 value) public returns (bool);
    function approve(address spender, uint256 value) public returns (bool);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event Transfer(address indexed from, address indexed to, uint256 value);
}


contract UniswapBasic {
    using SafeMath for uint256;

    event TokenPurchase(address indexed buyer, uint256 tokensPurchased, uint256 ethSpent);
    event EthPurchase(address indexed buyer, uint256 ethPurchased, uint256 tokensSpent);

    uint public constant feeRate = 500;        //fee is 1/feeRate = 0.2%

    uint256 public ethInMarket;
    uint256 public tokensInMarket;
    uint256 public invariant = 0;
    address public tokenAddress;
    ERC20Token token;

    function ethToTokens(uint256 minimumTokens, uint256 timeout) public payable {
        require(invariant > 0);
        require(msg.value != 0 && minimumTokens != 0 && now < timeout);
        uint256 fee = msg.value.div(feeRate);
        uint256 ethInPurchase = msg.value.sub(fee);
        uint256 newTotalEth = ethInMarket.add(ethInPurchase);
        uint256 newTotalTokens = invariant.div(newTotalEth);
        uint256 purchasedTokens = tokensInMarket.sub(newTotalTokens);
        require(purchasedTokens >= minimumTokens && purchasedTokens <= tokensInMarket);
        ethInMarket = newTotalEth;
        tokensInMarket = newTotalTokens;
        TokenPurchase(msg.sender, purchasedTokens, ethInPurchase);
        token.transfer(msg.sender, purchasedTokens);
    }


    function tokenToEth(uint256 sellQuantity, uint256 minimumEth, uint256 timeout) public {
        require(invariant > 0);
        require(sellQuantity !=0 && minimumEth != 0 && now < timeout);
        uint256 fee = sellQuantity.div(feeRate);
        uint256 tokensInPurchase = sellQuantity - fee;
        uint256 newTotalTokens = tokensInMarket.add(tokensInPurchase);
        uint256 newTotalEth = invariant.div(newTotalTokens);
        uint256 purchasedEth = ethInMarket.sub(newTotalEth);
        require(purchasedEth >= minimumEth && purchasedEth <= ethInMarket);
        tokensInMarket = newTotalTokens;
        ethInMarket = newTotalEth;
        EthPurchase(msg.sender, purchasedEth, tokensInPurchase);
        msg.sender.transfer(purchasedEth);
        token.transferFrom(msg.sender, address(this), sellQuantity);
    }
}


contract UniswapSharedLiquidity is UniswapBasic {
    using SafeMath for uint256;

    event Investment(address indexed liquidityProvider, uint256 indexed investedEth, uint256 indexed investedTokens);
    event Divestment(address indexed liquidityProvider, uint256 indexed divestedEth, uint256 indexed divestedTokens);

    mapping(address => uint256) liquidityBalance;
    mapping(address => uint256) divestedEthBalance;
    mapping(address => uint256) divestedTokenBalance;

    function uniswapSharedLiquidity(address _tokenAddress) public {
        tokenAddress = _tokenAddress;
        token = ERC20Token(tokenAddress);
    }


    function investLiquidity(uint256 tokenAmount) external payable {
        require(tokenAmount != 0 || msg.value != 0);
        require(tokenAmount >= 0);
        uint256 newTotalEth = ethInMarket.add(msg.value);
        uint256 newTotalTokens = tokensInMarket.add(tokenAmount);
        uint256 newInvariant = newTotalTokens.mul(newTotalEth);
        uint256 providedLiquidity = newInvariant.sub(invariant);
        liquidityBalance[msg.sender] = liquidityBalance[msg.sender].add(providedLiquidity);
        ethInMarket = newTotalEth;
        tokensInMarket = newTotalTokens;
        invariant = newInvariant;
        Investment(msg.sender, msg.value, tokenAmount);
        token.transferFrom(msg.sender, address(this), tokenAmount);
    }


    function divestLiquidity(uint256 divestedLiquidity) external {
        require(divestedLiquidity > 0);
        liquidityBalance[msg.sender] = liquidityBalance[msg.sender].sub(divestedLiquidity);
        uint256 newInvariant = invariant.sub(divestedLiquidity);
        uint256 ethTokenRatio = ethInMarket.div(tokensInMarket);
        uint256 newMarketTokensSquared = newInvariant.div(ethTokenRatio);
        uint256 newMarketTokens = sqrt(newMarketTokensSquared);
        uint256 newMarketEth = newInvariant.div(newMarketTokens);
        uint256 divestedEth = ethInMarket.sub(newMarketEth);
        uint256 divestedTokens = tokensInMarket.sub(newMarketTokens);
        divestedEthBalance[msg.sender] = divestedEth;
        divestedTokenBalance[msg.sender] = divestedTokens;
        ethInMarket = newMarketEth;
        tokensInMarket = newMarketTokens;
        invariant = newInvariant;
        Divestment(msg.sender, divestedEth, divestedTokens);
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


    function getLiquidityBalance(address provider) external view returns(uint256 balance){
        return liquidityBalance[provider];
    }


    function getDivestedBalances(address provider) external view returns(uint256 ethBal, uint256 tokBal){
        ethBal = divestedEthBalance[provider];
        tokBal = divestedTokenBalance[provider];
    }


    function sqrt(uint256 x) internal pure returns (uint256 y) {
        uint256 z = (x + 1) / 2;
        y = x;
        while (z < y) {
            y = z;
            z = (x / z + z) / 2;
        }
    }
}
