import React, { useState, useEffect } from 'react';
import { getApiKey, createApiKey, revokeApiKey } from '@libs/api';
import type { ApiKeyResponse } from '@libs/types';
import { authUtils } from '@libs/utils/auth';

type AuthMethod = 'oauth' | 'apikey';

const getBaseMcpUrl = (connectionUrl: string | undefined): string => {
  if (!connectionUrl) {
    const mcpBaseUrl = import.meta.env.PUBLIC_MCP_URL || window.location.origin;
    return `${mcpBaseUrl}/mcp`;
  }

  const lastSlashIndex = connectionUrl.lastIndexOf('/');
  if (lastSlashIndex === -1) {
    return connectionUrl;
  }

  const possibleKey = connectionUrl.substring(lastSlashIndex + 1);
  if (possibleKey.startsWith('sk_') || possibleKey.startsWith('SK_')) {
    return connectionUrl.substring(0, lastSlashIndex);
  }

  return connectionUrl;
};

const getMcpClients = (connectionUrl: string, authMethod: AuthMethod, baseMcpUrl: string) => [
  {
    id: 'claude',
    name: 'Anthropic Claude',
    description: 'Claude AI Assistant with advanced reasoning capabilities',
    supportsOAuth: true,
    instructions: authMethod === 'oauth'
      ? [
          'Open claude.ai',
          'Settings → Integrations',
          'Add Integration',
          'Integration name: MemCP',
          `Integration URL: ${baseMcpUrl}`,
          'Click "Connect" and sign in with GitHub when prompted'
        ]
      : [
          'Open claude.ai',
          'Settings → Integrations',
          'Add Integration',
          'Integration name: MemCP',
          `Integration URL: ${connectionUrl || 'Generate an API key first'}`
        ],
    hasCodeBlock: false
  },
  {
    id: 'cursor',
    name: 'Cursor',
    description: 'AI-powered code editor with MCP support',
    supportsOAuth: true,
    instructions: authMethod === 'oauth'
      ? [
          'Cursor → Settings → Cursor Settings',
          'MCP Tools → Edit → mcp.json',
          'Add the configuration below',
          'Cursor will prompt you to authenticate via browser'
        ]
      : [
          'Cursor → Settings → Cursor Settings',
          'MCP Tools → Edit → mcp.json',
          'Add the configuration below'
        ],
    hasCodeBlock: true,
    codeBlock: authMethod === 'oauth'
      ? JSON.stringify({
          "memcp": {
            "url": baseMcpUrl
          }
        }, null, 2)
      : JSON.stringify({
          "memcp": {
            "url": connectionUrl || "http://127.0.0.1:4200/mcp/"
          }
        }, null, 2)
  }
];

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
  const [selectedAuthMethod, setSelectedAuthMethod] = useState<AuthMethod>('oauth');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRevoking, setIsRevoking] = useState(false);
  const [copyFeedback, setCopyFeedback] = useState<{ [key: string]: boolean }>({});

  const baseMcpUrl = getBaseMcpUrl(apiKeyData?.connection_url);

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
        setError('Please log in to view your credentials');
        return;
      }

      const data = await getApiKey(token);
      setApiKeyData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch credentials');
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
      await fetchApiKey();
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
      await fetchApiKey();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke API key');
      console.error('Error revoking API key:', err);
    } finally {
      setIsRevoking(false);
    }
  };

  const handleCopyUrl = async (url: string, key: string) => {
    const success = await copyToClipboard(url);
    if (success) {
      showCopyFeedback(key);
    }
  };

  const handleCopyCodeBlock = async () => {
    const mcpClients = getMcpClients(apiKeyData?.connection_url || '', selectedAuthMethod, baseMcpUrl);
    const client = mcpClients.find(c => c.id === selectedClient);
    if (client?.codeBlock) {
      const success = await copyToClipboard(client.codeBlock);
      if (success) {
        showCopyFeedback('codeBlock');
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
    <div className="pt-16 md:pt-20 lg:pt-28 px-4 md:px-6 pb-4 md:pb-6 min-h-screen">
      <div className="max-w-7xl mx-auto h-full">
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 md:gap-6 lg:gap-8 min-h-[calc(100vh-5rem)] md:min-h-[calc(100vh-6rem)] lg:min-h-[calc(100vh-8rem)]">

          {/* Left Panel: Connection Methods */}
          <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-xl lg:rounded-2xl p-4 md:p-6 lg:p-8">
            <div className="h-full flex flex-col">
              <h2 className="text-xl md:text-2xl lg:text-3xl font-semibold text-white mb-6 md:mb-8 flex items-center">
                <svg className="w-8 h-8 mr-3 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Connection Methods
              </h2>

              {error && (
                <div className="mb-6 p-4 bg-red-500/20 border border-red-500/50 rounded-lg">
                  <p className="text-red-400">{error}</p>
                </div>
              )}

              <div className="space-y-4 md:space-y-6 flex-1">
                {/* OAuth Method - Recommended */}
                <div className="bg-gray-800/50 border-2 border-green-500/30 rounded-xl p-4 md:p-6 space-y-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg md:text-xl font-semibold text-white">OAuth Authentication</h3>
                        <span className="px-2.5 py-1 bg-green-500/20 border border-green-500/50 text-green-400 rounded-full text-xs font-semibold">
                          RECOMMENDED
                        </span>
                      </div>
                      <p className="text-gray-400 text-sm">
                        Modern, secure authentication. Supported by Cursor, Claude Desktop, and other OAuth-compatible clients.
                      </p>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-400 mb-2">MCP Server URL</label>
                      <div className="flex items-center gap-2">
                        <code className="flex-1 px-3 py-2.5 bg-gray-900 border border-gray-600 rounded-lg text-gray-300 font-mono text-sm">
                          {baseMcpUrl}
                        </code>
                        <button
                          onClick={() => handleCopyUrl(baseMcpUrl, 'oauthUrl')}
                          className="px-4 py-2.5 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/50 text-blue-400 rounded-lg transition-colors text-sm font-medium shrink-0"
                        >
                          {copyFeedback.oauthUrl ? (
                            <span className="flex items-center gap-2">
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                              Copied!
                            </span>
                          ) : 'Copy'}
                        </button>
                      </div>
                    </div>

                    <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
                      <div className="flex items-start gap-2">
                        <svg className="w-5 h-5 text-blue-400 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div className="text-sm text-blue-300">
                          <p className="font-medium mb-1">How it works:</p>
                          <ol className="list-decimal list-inside space-y-1 text-blue-300/90">
                            <li>Paste the URL above into your MCP client</li>
                            <li>Client will open a browser window</li>
                            <li>Sign in with GitHub to authorize access</li>
                            <li>Return to your client - you're connected!</li>
                          </ol>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* API Key Method - Legacy */}
                <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 md:p-6 space-y-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg md:text-xl font-semibold text-white">API Key Authentication</h3>
                        <span className="px-2.5 py-1 bg-gray-500/20 border border-gray-500/50 text-gray-400 rounded-full text-xs font-semibold">
                          LEGACY
                        </span>
                      </div>
                      <p className="text-gray-400 text-sm">
                        For clients that don't support OAuth. Less secure but more compatible.
                      </p>
                    </div>
                  </div>

                  {apiKeyData?.has_api_key ? (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-400 mb-2">API Key</label>
                        <div className="px-3 py-2.5 bg-gray-900 border border-gray-600 rounded-lg">
                          <code className="text-gray-300 font-mono text-sm break-all">
                            {apiKeyData.api_key || 'SK_••••••••'}
                          </code>
                        </div>
                        <p className="text-xs text-gray-500 mt-1.5">
                          Created: {apiKeyData.created_at ? new Date(apiKeyData.created_at).toLocaleDateString() : 'Unknown'}
                        </p>
                      </div>

                      <div>
                        <label className="block text-xs font-medium text-gray-400 mb-2">Connection URL (with API Key)</label>
                        <div className="flex items-center gap-2">
                          <code className="flex-1 px-3 py-2.5 bg-gray-900 border border-gray-600 rounded-lg text-gray-300 font-mono text-sm break-all">
                            {apiKeyData.connection_url || 'No connection URL available'}
                          </code>
                          <button
                            onClick={() => handleCopyUrl(apiKeyData.connection_url || '', 'apiKeyUrl')}
                            className="px-4 py-2.5 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/50 text-blue-400 rounded-lg transition-colors text-sm font-medium shrink-0"
                          >
                            {copyFeedback.apiKeyUrl ? (
                              <span className="flex items-center gap-2">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                                Copied!
                              </span>
                            ) : 'Copy'}
                          </button>
                        </div>
                      </div>

                      <button
                        onClick={handleRevokeApiKey}
                        disabled={isRevoking}
                        className="w-full px-4 py-2.5 bg-red-600/20 hover:bg-red-600/30 border border-red-500/50 text-red-400 rounded-lg transition-colors text-sm font-medium disabled:opacity-50"
                      >
                        {isRevoking ? 'Revoking...' : 'Revoke API Key'}
                      </button>
                    </div>
                  ) : (
                    <div className="text-center py-6">
                      <svg className="w-12 h-12 mx-auto mb-3 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                      </svg>
                      <p className="text-gray-400 text-sm mb-4">No API key generated yet</p>
                      <button
                        onClick={handleGenerateApiKey}
                        disabled={isGenerating}
                        className="px-6 py-2.5 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/50 text-purple-400 rounded-lg transition-colors text-sm font-medium disabled:opacity-50"
                      >
                        {isGenerating ? 'Generating...' : 'Generate API Key'}
                      </button>
                    </div>
                  )}

                  <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3">
                    <div className="flex items-start gap-2">
                      <svg className="w-5 h-5 text-amber-400 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                      </svg>
                      <p className="text-amber-300 text-xs">
                        <strong>Security Notice:</strong> The connection URL contains your API key. Treat it like a password.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Panel: MCP Client Setup */}
          <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-xl lg:rounded-2xl p-4 md:p-6 lg:p-8">
            <div className="h-full flex flex-col">
              <h2 className="text-xl md:text-2xl lg:text-3xl font-semibold text-white mb-6 md:mb-8 flex items-center">
                <svg className="w-6 h-6 md:w-8 md:h-8 mr-2 md:mr-3 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Client Setup Guide
              </h2>

              {/* Auth Method Selector */}
              <div className="mb-4 md:mb-6">
                <label className="block text-xs md:text-sm font-medium text-gray-300 mb-3">Authentication Method</label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={() => setSelectedAuthMethod('oauth')}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      selectedAuthMethod === 'oauth'
                        ? 'border-green-500/50 bg-green-500/10 text-white'
                        : 'border-gray-700 bg-gray-800/50 text-gray-400 hover:border-gray-600'
                    }`}
                  >
                    <div className="text-sm font-semibold">OAuth</div>
                    <div className="text-xs mt-1 opacity-75">Recommended</div>
                  </button>
                  <button
                    onClick={() => setSelectedAuthMethod('apikey')}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      selectedAuthMethod === 'apikey'
                        ? 'border-purple-500/50 bg-purple-500/10 text-white'
                        : 'border-gray-700 bg-gray-800/50 text-gray-400 hover:border-gray-600'
                    }`}
                  >
                    <div className="text-sm font-semibold">API Key</div>
                    <div className="text-xs mt-1 opacity-75">Legacy</div>
                  </button>
                </div>
              </div>

              {/* Client Selector */}
              <div className="mb-4 md:mb-6">
                <label className="block text-xs md:text-sm font-medium text-gray-300 mb-2 md:mb-3">Select MCP Client</label>
                <select
                  value={selectedClient}
                  onChange={(e) => setSelectedClient(e.target.value)}
                  className="w-full p-2 md:p-3 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm md:text-base focus:border-purple-500 focus:ring-1 focus:ring-purple-500 outline-none transition-colors"
                >
                  <option value="">Choose a client...</option>
                  {getMcpClients(apiKeyData?.connection_url || '', selectedAuthMethod, baseMcpUrl).map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.name} {client.supportsOAuth ? '(Supports OAuth)' : '(API Key only)'}
                    </option>
                  ))}
                </select>
              </div>

              {selectedClient && (
                <div className="space-y-4 md:space-y-6 flex-1">
                  {(() => {
                    const mcpClients = getMcpClients(apiKeyData?.connection_url || '', selectedAuthMethod, baseMcpUrl);
                    const client = mcpClients.find(c => c.id === selectedClient);
                    return client ? (
                      <>
                        {/* Client Info */}
                        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 md:p-6">
                          <h3 className="text-base md:text-lg font-medium text-white mb-2">{client.name}</h3>
                          <p className="text-gray-400 text-sm md:text-base">{client.description}</p>
                        </div>

                        {/* Setup Instructions */}
                        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 md:p-6">
                          <h4 className="text-sm md:text-md font-medium text-white mb-3 md:mb-4 flex items-center">
                            <svg className="w-4 h-4 md:w-5 md:h-5 mr-2 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Setup Instructions
                          </h4>
                          <ol className="space-y-2">
                            {client.instructions.map((step, index) => (
                              <li key={index} className="flex items-start space-x-2 md:space-x-3">
                                <span className="flex-shrink-0 w-5 h-5 md:w-6 md:h-6 bg-purple-600 text-white rounded-full text-xs md:text-sm flex items-center justify-center font-medium">
                                  {index + 1}
                                </span>
                                <span className="text-gray-300 text-sm md:text-base">{step}</span>
                              </li>
                            ))}
                          </ol>
                        </div>

                        {/* Code Block */}
                        {client.hasCodeBlock && client.codeBlock && (
                          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 md:p-6">
                            <div className="flex items-center justify-between mb-3">
                              <h4 className="text-sm md:text-md font-medium text-white flex items-center">
                                <svg className="w-4 h-4 md:w-5 md:h-5 mr-2 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                                </svg>
                                Configuration
                              </h4>
                              <button
                                onClick={handleCopyCodeBlock}
                                className="px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/50 text-blue-400 rounded-md transition-colors text-xs font-medium"
                              >
                                {copyFeedback.codeBlock ? (
                                  <span className="flex items-center gap-1">
                                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                    </svg>
                                    Copied!
                                  </span>
                                ) : 'Copy'}
                              </button>
                            </div>
                            <pre className="bg-gray-900 border border-gray-600 rounded-lg p-4 overflow-x-auto">
                              <code className="text-gray-300 text-sm font-mono whitespace-pre">
                                {client.codeBlock}
                              </code>
                            </pre>
                          </div>
                        )}

                        {selectedAuthMethod === 'apikey' && !apiKeyData?.connection_url && (
                          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 text-center">
                            <svg className="w-12 h-12 mx-auto mb-2 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                            </svg>
                            <p className="text-yellow-300 text-sm">
                              Generate an API key first to use this authentication method
                            </p>
                          </div>
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
                  <p className="text-gray-400">Choose a client to see setup instructions based on your selected authentication method.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
