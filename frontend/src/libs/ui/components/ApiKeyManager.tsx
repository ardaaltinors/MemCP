import { useState, useEffect } from 'react';
import { getApiKey, createApiKey, revokeApiKey } from '../../api';
import { authUtils } from '../../utils/auth';
import type { ApiKeyResponse } from '../../types';

export function ApiKeyManager() {
  const [apiKeyData, setApiKeyData] = useState<ApiKeyResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [isRevoking, setIsRevoking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  // Load API key data on component mount
  useEffect(() => {
    loadApiKey();
  }, []);

  const loadApiKey = async () => {
    try {
      setError(null);
      setIsLoading(true);
      
      const token = authUtils.getToken();
      if (!token) {
        throw new Error('No authentication token found');
      }

      const data = await getApiKey(token);
      setApiKeyData(data);
    } catch (err) {
      console.error('Error loading API key:', err);
      setError(err instanceof Error ? err.message : 'Failed to load API key');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateApiKey = async () => {
    try {
      setError(null);
      setIsCreating(true);
      
      const token = authUtils.getToken();
      if (!token) {
        throw new Error('No authentication token found');
      }

      const newApiKey = await createApiKey(token);
      
      // Update the state with the new API key
      setApiKeyData({
        has_api_key: true,
        api_key: newApiKey.api_key,
        created_at: newApiKey.created_at
      });
      setToastMessage('API Key created successfully!');
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3000); // Hide after 3 seconds
    } catch (err) {
      console.error('Error creating API key:', err);
      setError(err instanceof Error ? err.message : 'Failed to create API key');
    } finally {
      setIsCreating(false);
    }
  };

  const handleRevokeApiKey = async () => {
    try {
      setError(null);
      setIsRevoking(true);
      
      const token = authUtils.getToken();
      if (!token) {
        throw new Error('No authentication token found');
      }

      await revokeApiKey(token);
      
      // Update the state to reflect no API key
      setApiKeyData({
        has_api_key: false
      });
      setToastMessage('API Key revoked successfully!');
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3000); // Hide after 3 seconds
    } catch (err) {
      console.error('Error revoking API key:', err);
      setError(err instanceof Error ? err.message : 'Failed to revoke API key');
    } finally {
      setIsRevoking(false);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setToastMessage('Copied to clipboard!');
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3000); // Hide after 3 seconds
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span className="text-gray-300">Loading API key...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Error Display */}
      {error && (
        <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {showToast && (
        <div className="fixed bottom-4 right-4 bg-gray-900 text-white px-4 py-2 rounded-lg shadow-lg text-sm">
          {toastMessage}
        </div>
      )}

      {/* Action Buttons */}
      {!apiKeyData?.has_api_key && (
        <div className="flex gap-3">
          <button
            onClick={handleCreateApiKey}
            disabled={isCreating}
            className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-800 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center"
          >
            {isCreating ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Creating...
              </>
            ) : (
              'Create API Key'
            )}
          </button>
        </div>
      )}

      {/* API Key Display */}
      {apiKeyData?.has_api_key && apiKeyData.api_key && (
        <div className="bg-gray-800/50 border border-gray-600 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center">
              <span className="inline-block w-2 h-2 rounded-full mr-2 bg-green-400"></span>
              <span className="text-sm text-gray-400">
                Created: {apiKeyData.created_at ? formatDate(apiKeyData.created_at) : 'Unknown'}
              </span>
            </div>
            <button
              onClick={handleRevokeApiKey}
              disabled={isRevoking}
              className="text-red-400 hover:text-red-300 text-sm font-medium transition-colors disabled:opacity-50"
            >
              {isRevoking ? 'Revoking...' : 'Revoke'}
            </button>
          </div>

          {/* API Key */}
          <div className="mb-3">
            <label className="block text-xs font-medium text-gray-400 mb-1">
              API Key
            </label>
            <div className="flex items-center bg-gray-900 border border-gray-600 rounded p-2">
              <code className="text-sm text-gray-300 font-mono flex-1 break-all">
                {apiKeyData.api_key}
              </code>
              <button
                onClick={() => copyToClipboard(apiKeyData.api_key!)}
                className="ml-2 p-1 hover:bg-gray-700 rounded transition-colors"
                title="Copy to clipboard"
              >
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 002 2v8a2 2 0 002 2z" />
                </svg>
              </button>
            </div>
          </div>

          {/* Connection URL */}
          <div className="mb-3">
            <label className="block text-xs font-medium text-gray-400 mb-1">
              Connection URL
            </label>
            <div className="flex items-center bg-gray-900 border border-gray-600 rounded p-2">
              <code className="text-sm text-gray-300 font-mono flex-1 break-all">
              {apiKeyData.connection_url}
              </code>
              <button
                onClick={() => copyToClipboard(apiKeyData.connection_url!)}
                className="ml-2 p-1 hover:bg-gray-700 rounded transition-colors"
                title="Copy to clipboard"
              >
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 002 2v8a2 2 0 002 2z" />
                </svg>
              </button>
            </div>
          </div>

          {/* Warning */}
          <div className="bg-yellow-900/20 border border-yellow-700/50 rounded-lg p-3">
            <div className="flex">
              <svg className="w-5 h-5 text-yellow-400 mr-2 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.728-.833-2.498 0L4.316 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <div>
                <p className="text-yellow-400 text-sm font-medium">Caution</p>
                <p className="text-yellow-200 text-xs mt-1">
                  Treat your MCP server URL like a password! It can be used to run tools attached to this server and access your data.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* No API Key State */}
      {!apiKeyData?.has_api_key && !isCreating && (
        <div className="text-center py-8 text-gray-400">
          <svg className="w-12 h-12 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m-2-2a2 2 0 00-2 2m2-2v2a2 2 0 01-2 2m-2-2H9m10 0a2 2 0 01-2 2H9a2 2 0 01-2-2m2 2V9a2 2 0 012-2m0 0V7a2 2 0 011-1 2 2 0 011 1v1a2 2 0 01-1 1" />
          </svg>
          <p>No API key created yet</p>
          <p className="text-sm mt-1">Create your API key to get started</p>
        </div>
      )}
    </div>
  );
} 