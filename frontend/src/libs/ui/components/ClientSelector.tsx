import { useState } from 'react';

interface Client {
  id: string;
  name: string;
  icon: string;
  description: string;
}

const clients: Client[] = [
  {
    id: 'claude',
    name: 'Claude',
    icon: '🤖',
    description: 'Anthropic Claude AI Assistant'
  },
  {
    id: 'cursor',
    name: 'Cursor',
    icon: '⚡',
    description: 'AI-powered code editor'
  },
  {
    id: 'vscode',
    name: 'VS Code',
    icon: '📝',
    description: 'Visual Studio Code extension'
  },
  {
    id: 'sublime',
    name: 'Sublime Text',
    icon: '✨',
    description: 'Sublime Text plugin'
  },
  {
    id: 'neovim',
    name: 'Neovim',
    icon: '🚀',
    description: 'Neovim integration'
  }
];

export function ClientSelector() {
  const [selectedClient, setSelectedClient] = useState<Client>(clients[0]);
  const [isOpen, setIsOpen] = useState(false);

  const handleClientSelect = (client: Client) => {
    setSelectedClient(client);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <label className="block text-sm font-medium text-gray-300 mb-2">
        Select MCP Client
      </label>
      
      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-3 text-left hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <span className="text-lg mr-3">{selectedClient.icon}</span>
              <div>
                <div className="text-white font-medium">{selectedClient.name}</div>
                <div className="text-gray-400 text-sm">{selectedClient.description}</div>
              </div>
            </div>
            <svg
              className={`w-5 h-5 text-gray-400 transition-transform duration-200 ${
                isOpen ? 'rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </button>

        {/* Dropdown Menu */}
        {isOpen && (
          <div className="absolute z-10 w-full mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-xl max-h-60 overflow-auto">
            {clients.map((client) => (
              <button
                key={client.id}
                onClick={() => handleClientSelect(client)}
                className={`w-full px-4 py-3 text-left hover:bg-gray-700 focus:outline-none focus:bg-gray-700 transition-colors ${
                  selectedClient.id === client.id ? 'bg-gray-700' : ''
                }`}
              >
                <div className="flex items-center">
                  <span className="text-lg mr-3">{client.icon}</span>
                  <div>
                    <div className="text-white font-medium">{client.name}</div>
                    <div className="text-gray-400 text-sm">{client.description}</div>
                  </div>
                  {selectedClient.id === client.id && (
                    <svg
                      className="w-5 h-5 text-blue-400 ml-auto"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Setup Instructions */}
      <div className="mt-4 p-4 bg-gray-800/50 border border-gray-600 rounded-lg">
        <h4 className="text-sm font-medium text-gray-300 mb-2">Setup Instructions</h4>
        <div className="text-sm text-gray-400 space-y-2">
          {selectedClient.id === 'claude' && (
            <div>
              <p>1. Open claude.ai</p>
              <p>2. Settings → Integrations</p>
              <p>3. Add Integration</p>
              <p>4. Integration name: MemCP</p>
              <p>5. Integration URL: Your connection URL</p>
            </div>
          )}
          {selectedClient.id === 'cursor' && (
            <div>
              <p>1. Cursor → Settings → Cursor Settings</p>
              <p>2. MCP Tools → Edit → mcp.json</p>
              <p>3. Add: {"{"}"memcp": {"{"}"url": "http://127.0.0.1:4200/mcp/"{"}"}{"}"}{"}"}</p>
            </div>
          )}
          {selectedClient.id === 'vscode' && (
            <div>
              <p>1. Install the MCP extension</p>
              <p>2. Open command palette (Cmd/Ctrl+Shift+P)</p>
              <p>3. Run "MCP: Add Server"</p>
            </div>
          )}
          {selectedClient.id === 'sublime' && (
            <div>
              <p>1. Install Package Control</p>
              <p>2. Install "MCP Client" package</p>
              <p>3. Configure in user settings</p>
            </div>
          )}
          {selectedClient.id === 'neovim' && (
            <div>
              <p>1. Install the MCP plugin via your package manager</p>
              <p>2. Add configuration to your init.lua</p>
              <p>3. Restart Neovim</p>
            </div>
          )}
        </div>
      </div>

      {/* Quick Copy */}
      <div className="mt-3">
        <button
          onClick={() => {
            // This would copy setup instructions or connection details
            navigator.clipboard.writeText(`Selected client: ${selectedClient.name}`);
          }}
          className="w-full text-sm text-blue-400 hover:text-blue-300 transition-colors flex items-center justify-center py-2"
        >
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          Copy client info
        </button>
      </div>
    </div>
  );
} 