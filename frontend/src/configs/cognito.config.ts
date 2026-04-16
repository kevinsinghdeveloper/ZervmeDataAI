export const COGNITO_CONFIG = {
  REGION: process.env.REACT_APP_COGNITO_REGION || 'us-east-1',
  USER_POOL_ID: process.env.REACT_APP_COGNITO_USER_POOL_ID || '',
  CLIENT_ID: process.env.REACT_APP_COGNITO_CLIENT_ID || '',
};
