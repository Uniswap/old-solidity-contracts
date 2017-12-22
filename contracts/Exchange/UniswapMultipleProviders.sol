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
    uint256 public invariant;
    uint256 public feePool;
    address public tokenAddress;
    ERC20Token token;

    function ethToTokens(uint256 minimumTokens, uint256 timeout) public payable {
        require(invariant > 0);
        require(msg.value != 0 && minimumTokens != 0 && now < timeout);
        uint256 fee = msg.value.div(feeRate);
        uint256 ethSold = msg.value.sub(fee);
        uint256 newEthInMarket = ethInMarket.add(ethSold);
        uint256 newTokensInMarket = invariant.div(newEthInMarket);
        uint256 purchasedTokens = tokensInMarket.sub(newTokensInMarket);
        require(purchasedTokens >= minimumTokens && purchasedTokens <= tokensInMarket);
        feePool = feePool.add(fee);
        ethInMarket = newEthInMarket;
        tokensInMarket = newTokensInMarket;
        TokenPurchase(msg.sender, purchasedTokens, ethSold);
        token.transfer(msg.sender, purchasedTokens);
    }


    function fallbackEthToTokens(address buyer, uint256 value) internal {
        require(invariant > 0);
        uint256 fee = value.div(feeRate);
        uint256 ethSold = value.sub(fee);
        uint256 newEthInMarket = ethInMarket.add(ethSold);
        uint256 newTokensInMarket = invariant.div(newEthInMarket);
        uint256 purchasedTokens = tokensInMarket.sub(newTokensInMarket);
        require(purchasedTokens <= tokensInMarket.div(10)); //cannot buy more than 10% of tokens through fallback function
        feePool = feePool.add(fee);
        ethInMarket = newEthInMarket;
        tokensInMarket = newTokensInMarket;
        TokenPurchase(buyer, purchasedTokens, ethSold);
        token.transfer(buyer, purchasedTokens);
    }


    function tokenToEth(uint256 tokensSold, uint256 minimumEth, uint256 timeout) public {
        require(invariant > 0);
        require(tokensSold !=0 && minimumEth != 0 && now < timeout);
        uint256 newTokensInMarket = tokensInMarket.add(tokensSold);
        uint256 newEthInMarket = invariant.div(newTokensInMarket);
        uint256 purchasedEth = ethInMarket.sub(newEthInMarket);
        uint256 fee = purchasedEth.div(feeRate);
        uint256 ethToBuyer = purchasedEth.sub(fee);
        require(ethToBuyer >= minimumEth && purchasedEth <= ethInMarket);
        feePool = feePool.add(fee);
        tokensInMarket = newTokensInMarket;
        ethInMarket = newEthInMarket;
        EthPurchase(msg.sender, purchasedEth, tokensSold);
        msg.sender.transfer(purchasedEth);
        token.transferFrom(msg.sender, address(this), tokensSold);
    }
}


contract UniswapMultipleProviders is UniswapBasic {
    using SafeMath for uint256;

    event Investment(address indexed liquidityProvider, uint256 indexed sharesPurchased);
    event Divestment(address indexed liquidityProvider, uint256 indexed sharesSold);

    uint256 public totalShares;
    uint256 public lastFeeDistribution;
    mapping(address => uint256) liquidityShares;
    mapping(address => uint256) divestedEthBalance;
    mapping(address => uint256) divestedTokenBalance;
    mapping(address => uint256) feeBalance;
    mapping(address => bool) isInvestor;
    address[] investors;

    modifier waitingPeriod() {
        uint lockoutEnd = lastFeeDistribution.add(1 weeks);
        require(now > lockoutEnd);
        _;
    }

    function UniswapMultipleProviders(address _tokenAddress) public {
        tokenAddress = _tokenAddress;
        token = ERC20Token(tokenAddress);
        lastFeeDistribution = now;
    }


    function() public payable {
        require(msg.value != 0);
        fallbackEthToTokens(msg.sender, msg.value);
    }

    // Needs work - numbers are somewhat arbitrary right now
    function initializeExchange(uint256 tokenAmount) external payable {
        require(invariant == 0 && totalShares == 0);
        require(msg.value >= 1000000 && tokenAmount >= 1000000);
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
        if(isInvestor[msg.sender] == false) {
            isInvestor[msg.sender] == true;
            investors.push(msg.sender);
        }
        Investment(msg.sender, sharesPurchased);
        token.transferFrom(msg.sender, address(this), tokensRequired);
    }


    function divestLiquidity(uint256 sharesSold) external {
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
        invariant = ethInMarket.mul(tokensInMarket);
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


    function getShares(address provider) external view returns(uint256 shares){
        return liquidityShares[provider];
    }


    function getDivestedBalances(address provider) external view returns(uint256 ethBal, uint256 tokBal){
        ethBal = divestedEthBalance[provider];
        tokBal = divestedTokenBalance[provider];
    }


    // Needs to be replaced
    // https://medium.com/@weka/dividend-bearing-tokens-on-ethereum-42d01c710657
    function distributeFees() public waitingPeriod {
        for (uint i = 0; i < investors.length; i++) {
          address investor = investors[i];
          uint256 newFees = feePool * (liquidityShares[investor] / totalShares);
          feeBalance[investor] = feeBalance[investor].add(newFees);
        }

        lastFeeDistribution = now;
    }
}
