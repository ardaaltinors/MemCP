import React, { useState, useEffect } from 'react';
import { getApiKey, createApiKey, revokeApiKey } from '@libs/api';
import type { ApiKeyResponse } from '@libs/types';
import { authUtils } from '@libs/utils/auth';

// MCP Client configuration
const MCP_CLIENTS = [
  {
    id: 'claude',
    name: 'Anthropic Claude',
    description: 'Claude AI Assistant with advanced reasoning capabilities',
    instructions: [
      'Open Claude and go to Settings',
      'Navigate to MCP Settings',
      'Add your connection URL',
      'Save the configuration'
    ]
  },
  {
    id: 'openai',
    name: 'OpenAI ChatGPT',
    description: 'ChatGPT with custom plugins and extensions',
    instructions: [
      'Open ChatGPT Settings',
      'Go to Plugins & Extensions',
      'Add MCP Connection',
      'Enter your connection URL'
    ]
  }
];

// Copy to clipboard utility
const copyToClipboard = async (text: string): Promise<boolean> => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    console.error('Failed to copy text: ', err);
    return false;
  }
};

export const CredentialsContainer: React.FC = () => {
  const [apiKeyData, setApiKeyData] = useState<ApiKeyResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedClient, setSelectedClient] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRevoking, setIsRevoking] = useState(false);
  const [copyFeedback, setCopyFeedback] = useState<{ [key: string]: boolean }>({});

  const showCopyFeedback = (key: string) => {
    setCopyFeedback(prev => ({ ...prev, [key]: true }));
    setTimeout(() => {
      setCopyFeedback(prev => ({ ...prev, [key]: false }));
    }, 2000);
  };

  const fetchApiKey = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const token = authUtils.getToken();

      if (!token) {
        setError('Please log in to view your API keys');
        return;
      }

      const data = await getApiKey(token);
      setApiKeyData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch API key');
      console.error('Error fetching API key:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateApiKey = async () => {
    try {
      setIsGenerating(true);
      setError(null);
      const token = authUtils.getToken();

      if (!token) {
        setError('Please log in to generate API key');
        return;
      }

      await createApiKey(token);
      await fetchApiKey(); // Refresh the data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate API key');
      console.error('Error generating API key:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRevokeApiKey = async () => {
    try {
      setIsRevoking(true);
      setError(null);
      const token = authUtils.getToken();

      if (!token) {
        setError('Please log in to revoke API key');
        return;
      }

      await revokeApiKey(token);
      await fetchApiKey(); // Refresh the data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke API key');
      console.error('Error revoking API key:', err);
    } finally {
      setIsRevoking(false);
    }
  };

  const handleCopyConnectionUrl = async () => {
    if (apiKeyData?.connection_url) {
      const success = await copyToClipboard(apiKeyData.connection_url);
      if (success) {
        showCopyFeedback('connectionUrl');
      }
    }
  };

  const handleCopyClientInfo = async () => {
    const client = MCP_CLIENTS.find(c => c.id === selectedClient);
    if (client && apiKeyData?.connection_url) {
      const clientInfo = `Client: ${client.name}\nConnection URL: ${apiKeyData.connection_url}\nInstructions:\n${client.instructions
        .map((step, i) => `${i + 1}. ${step}`)
        .join('\n')}`;
      const success = await copyToClipboard(clientInfo);
      if (success) {
        showCopyFeedback('clientInfo');
      }
    }
  };

  useEffect(() => {
    fetchApiKey();
  }, []);

  if (isLoading) {
    return (
      <div className="h-[calc(100vh-6rem)] flex items-center justify-center">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute inset-0 border-4 border-purple-200 rounded-full animate-ping"></div>
            <div className="absolute inset-0 border-4 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
          <p className="text-gray-300 text-lg">Loading credentials...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="pt-28 px-6 pb-6 h-screen">
      <div className="max-w-7xl mx-auto h-full">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-full">

          {/* Left Panel: Your API Keys */}
          <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-8">
            <div className="h-full flex flex-col">
              <h2 className="text-3xl font-semibold text-white mb-8 flex items-center">
                <svg className="w-8 h-8 mr-3 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                </svg>
                Your API Keys
              </h2>

              {error && (
                <div className="mb-6 p-4 bg-red-500/20 border border-red-500/50 rounded-lg">
                  <p className="text-red-400">{error}</p>
                </div>
              )}

              {apiKeyData?.has_api_key ? (
                <div className="space-y-6 flex-1">
                  {/* API Key Card */}
                  <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6 space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-medium text-white">API Key</h3>
                      <span className="text-sm text-gray-400">
                        Created: {apiKeyData.created_at ? new Date(apiKeyData.created_at).toLocaleDateString() : 'Unknown'}
                      </span>
                    </div>

                    <div className="flex items-center">
                      <code className="flex-1 px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-gray-300 font-mono break-all">
                        {apiKeyData.api_key || 'SK_••••••••'}
                      </code>
                    </div>

                    {/* Connection URL */}
                    <div className="flex items-center space-x-3">
                      <code className="flex-1 px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-gray-300 font-mono text-sm break-all">
                        {apiKeyData.connection_url || 'No connection URL available'}
                      </code>
                      <button
                        onClick={handleCopyConnectionUrl}
                        className="px-4 py-2 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/50 text-blue-400 rounded-lg transition-colors text-sm font-medium"
                      >
                        {copyFeedback.connectionUrl ? 'Copied!' : 'Copy'}
                      </button>
                    </div>

                    <button
                      onClick={handleRevokeApiKey}
                      disabled={isRevoking}
                      className="w-full px-4 py-2 bg-red-600/20 hover:bg-red-600/30 border border-red-500/50 text-red-400 rounded-lg transition-colors font-medium disabled:opacity-50"
                    >
                      {isRevoking ? 'Revoking...' : 'Revoke Key'}
                    </button>
                  </div>

                  {/* Security Warning */}
                  <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4">
                    <div className="flex items-start space-x-3">
                      <svg className="w-5 h-5 text-amber-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                      </svg>
                      <p className="text-amber-300 text-sm">
                        <strong>Security Notice:</strong> Treat your MCP server URL like a password. It can be used to run tools and access your data.
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center">
                  <div className="w-20 h-20 mx-auto mb-6 bg-purple-500/20 rounded-full flex items-center justify-center">
                    <svg className="w-10 h-10 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1721 9z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">No API Key Generated</h3>
                  <p className="text-gray-400 mb-8">Generate your first API key to start using MCP connections.</p>
                </div>
              )}

              {/* Generate New Key Button */}
              <button
                onClick={handleGenerateApiKey}
                disabled={isGenerating}
                className="w-full group relative overflow-hidden rounded-xl transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]"
              >
                {/* Gradient Border Effect */}
                <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 opacity-80 blur-sm group-hover:opacity-100 transition-opacity"></div>

                {/* Button Background */}
                <div className="relative bg-gray-900 rounded-xl border border-gray-700 group-hover:border-transparent transition-colors">
                  <div className="px-6 py-4 flex items-center justify-center space-x-3">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    <span className="text-white font-medium text-lg">
                      {isGenerating ? 'Generating...' : 'Generate New Key'}
                    </span>
                  </div>
                </div>
              </button>
            </div>
          </div>

          {/* Right Panel: MCP Client */}
          <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-8">
            <div className="h-full flex flex-col">
              <h2 className="text-3xl font-semibold text-white mb-8 flex items-center">
                <svg className="w-8 h-8 mr-3 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                MCP Client
              </h2>

              {/* Client Selector */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-300 mb-3">Select MCP Client</label>
                <select
                  value={selectedClient}
                  onChange={(e) => setSelectedClient(e.target.value)}
                  className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-purple-500 focus:ring-1 focus:ring-purple-500 outline-none transition-colors"
                >
                  <option value="">Choose a client...</option>
                  {MCP_CLIENTS.map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.name}
                    </option>
                  ))}
                </select>
              </div>

              {selectedClient && (
                <div className="space-y-6 flex-1">
                  {(() => {
                    const client = MCP_CLIENTS.find(c => c.id === selectedClient);
                    return client ? (
                      <>
                        {/* Client Info */}
                        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
                          <h3 className="text-lg font-medium text-white mb-2">{client.name}</h3>
                          <p className="text-gray-400">{client.description}</p>
                        </div>

                        {/* Setup Instructions */}
                        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
                          <h4 className="text-md font-medium text-white mb-4 flex items-center">
                            <svg className="w-5 h-5 mr-2 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Setup Instructions
                          </h4>
                          <ol className="space-y-2">
                            {client.instructions.map((step, index) => (
                              <li key={index} className="flex items-start space-x-3">
                                <span className="flex-shrink-0 w-6 h-6 bg-purple-600 text-white rounded-full text-sm flex items-center justify-center font-medium">
                                  {index + 1}
                                </span>
                                <span className="text-gray-300">{step}</span>
                              </li>
                            ))}
                          </ol>
                        </div>

                        {/* Copy Client Info Button */}
                        <button
                          onClick={handleCopyClientInfo}
                          disabled={!apiKeyData?.connection_url}
                          className="w-full px-6 py-4 bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/50 text-emerald-400 rounded-xl transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {copyFeedback.clientInfo ? 'Copied!' : 'Copy Client Info'}
                        </button>

                        {!apiKeyData?.connection_url && (
                          <p className="text-sm text-gray-500 text-center">
                            Generate an API key first to enable client setup
                          </p>
                        )}
                      </>
                    ) : null;
                  })()}
                </div>
              )}

              {!selectedClient && (
                <div className="flex-1 flex flex-col items-center justify-center text-center">
                  <div className="w-20 h-20 mx-auto mb-6 bg-blue-500/20 rounded-full flex items-center justify-center">
                    <svg className="w-10 h-10 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">Select an MCP Client</h3>
                  <p className="text-gray-400">Choose a client to see setup instructions and connection details.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
