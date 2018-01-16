pragma solidity ^0.4.18;
import "./UniswapExchange.sol";


contract FactoryInterface {
    address[] public tokenList;
    mapping(address => bool) exchangeExists;
    mapping(address => address) tokenExchanges;
    function createExchange(address token) public returns (address exchange);
    function getExchangeCount() public view returns (uint exchangeCount);
    function tokenToExchangeLookup(address token) public view returns (address exchange);
    function exchangeToTokenLookup(address token) public view returns (address exchange);
}


contract UniswapFactory is FactoryInterface {

    // index of tokens with registered exchanges
    address[] public tokenList;
    mapping(address => address) tokenToExchange;
    mapping(address => address) exchangeToToken;

    function createExchange(address token) public returns (address exchange) {
        require(tokenToExchange[token] == address(0));      //There can only be one exchange per token
        require(token != address(0) && token != address(this));
        UniswapExchange newExchange = new UniswapExchange(token);
        tokenList.push(token);
        tokenToExchange[token] = newExchange;
        exchangeToToken[newExchange] = token;
        return newExchange;
    }

    function getExchangeCount() public view returns (uint exchangeCount) {
        return tokenList.length;
    }

    function tokenToExchangeLookup(address token) public view returns (address exchange) {
        return tokenToExchange[token];
    }

    function exchangeToTokenLookup(address exchange) public view returns (address token) {
        return exchangeToToken[exchange];
    }
}
