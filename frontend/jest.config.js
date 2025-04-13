module.exports = {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  transform: {
    "^.+\\.(ts|tsx)$": "ts-jest",              // Transforms TypeScript files
    "^.+\\.(js|jsx|mjs)$": "babel-jest",       // Transforms JavaScript files, including ES modules
  },
  transformIgnorePatterns: [
    "/node_modules/(?!(axios|other-esm-dependency)/)", // Ensures axios is transformed
  ],
  setupFilesAfterEnv: ["frontend/jest.setup.js"],     // Ensures Jest setup file is loaded
  
  // Coverage configuration
  collectCoverage: true,   // Enable coverage collection
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',  // Specify which files to collect coverage from
    '!src/index.js',              // Exclude specific files
    '!src/serviceWorker.js',
    '!src/reportWebVitals.js',
  ],
  coverageDirectory: 'coverage', // Output directory for coverage reports
  coverageReporters: ['text', 'lcov', 'html'], // Coverage report formats
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};

