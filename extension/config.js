// Extension Configuration
// Change these values based on your deployment environment

const CONFIG = {
  // For local development
  development: {
    frontendUrl: 'http://localhost:3000',
    backendUrl: 'http://localhost:8000'
  },
  
  // For production
  production: {
    frontendUrl: 'https://pulsenews.app',
    backendUrl: 'https://api.pulsenews.app'
  }
};

// Set environment here (change to 'production' when deploying)
const ENVIRONMENT = 'development';

// Export current config
const CURRENT_CONFIG = CONFIG[ENVIRONMENT];
