pragma solidity ^0.4.18;
import "./UniswapTokenToToken.sol";


contract FactoryInterface {
    address[] public tokenList;
    mapping(address => bool) exchangeExists;
    mapping(address => address) tokenExchanges;
    function createExchange(address token) public returns (address exchange);
    function getExchangeCount() public view returns (uint exchangeCount);
    function doesExchangeExist(address token) public view returns (bool);
    function tokenExchangeLookup(address token) public view returns (address exchange);
}


contract UniswapFactory is FactoryInterface {

    // index of tokens with registered exchanges
    address[] public tokenList;

    // Mapping of token addresses to exchanges
    mapping(address => bool) exchangeExists;
    mapping(address => address) tokenExchanges;


    function createExchange(address token) public returns (address exchange) {
        require(!exchangeExists[token]);
        require(token != address(0));
        UniswapTokenToToken newExchange = new UniswapTokenToToken(token);
        tokenList.push(token);
        tokenExchanges[token] = newExchange;
        exchangeExists[token] = true;
        return newExchange;
    }


    function getExchangeCount() public view returns (uint exchangeCount) {
        return tokenList.length;
    }


    function doesExchangeExist(address token) public view returns (bool) {
        return exchangeExists[token];
    }


    function tokenExchangeLookup(address token) public view returns (address exchange) {
        require(exchangeExists[token]);
        return tokenExchanges[token];
    }
}
