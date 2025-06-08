import type { Token } from "../types";

// Storage keys
const AUTH_TOKEN_KEY = 'authToken';
const TOKEN_TYPE_KEY = 'tokenType';
const TOKEN_EXPIRY_KEY = 'tokenExpiry';

export const authUtils = {
  // Store token in localStorage
  storeToken: (token: Token) => {
    localStorage.setItem(AUTH_TOKEN_KEY, token.access_token);
    localStorage.setItem(TOKEN_TYPE_KEY, token.token_type);
    localStorage.setItem(TOKEN_EXPIRY_KEY, token.expires_at);
  },

  // Get token from localStorage
  getToken: (): string | null => {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  },

  // Get full token info
  getTokenInfo: (): { token: string; type: string; expiresAt: string } | null => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    const type = localStorage.getItem(TOKEN_TYPE_KEY);
    const expiresAt = localStorage.getItem(TOKEN_EXPIRY_KEY);

    if (!token || !type || !expiresAt) {
      return null;
    }

    return { token, type, expiresAt };
  },

  // Check if token exists and is not expired
  isAuthenticated: (): boolean => {
    const tokenInfo = authUtils.getTokenInfo();
    
    if (!tokenInfo) {
      return false;
    }

    // Check if token is expired
    const expiryDate = new Date(tokenInfo.expiresAt);
    const now = new Date();
    
    return expiryDate > now;
  },

  // Clear all auth data
  clearAuth: () => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(TOKEN_TYPE_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
  },

  // Get authorization header value
  getAuthHeader: (): string | null => {
    const tokenInfo = authUtils.getTokenInfo();
    
    if (!tokenInfo || !authUtils.isAuthenticated()) {
      return null;
    }

    return `${tokenInfo.type} ${tokenInfo.token}`;
  }
}; 