const path = require('path');

module.exports = {
  stats: {
    // Suppress CommonJS warnings in development
    warnings: false,
    warningsFilter: [
      /commonjs/i,
      /Critical dependency/i,
      /Module parse failed/i
    ]
  },
  resolve: {
    fallback: {
      "crypto": false,
      "stream": false,
      "assert": false,
      "http": false,
      "https": false,
      "os": false,
      "url": false,
      "zlib": false
    }
  },
  ignoreWarnings: [
    /Critical dependency: the request of a dependency is an expression/,
    /Critical dependency: require function is used in a way/,
    /Module parse failed: Unexpected token/,
    /export .* was not found in/,
    /Can't resolve 'crypto'/,
    /Can't resolve 'stream'/,
    /commonjs/i
  ]
};