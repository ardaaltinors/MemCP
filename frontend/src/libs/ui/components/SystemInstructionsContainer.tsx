import React, { useState } from 'react';
import { MEMCP_SYSTEM_PROMPT } from '@libs/constants/memcpSystemPrompt';

export const SystemInstructionsContainer: React.FC = () => {
  const [copyFeedback, setCopyFeedback] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleCopyPrompt = async () => {
    try {
      await navigator.clipboard.writeText(MEMCP_SYSTEM_PROMPT);
      setCopyFeedback(true);
      setTimeout(() => {
        setCopyFeedback(false);
      }, 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const previewLines = MEMCP_SYSTEM_PROMPT.split('\n').slice(0, 8).join('\n');
  const isLongPrompt = MEMCP_SYSTEM_PROMPT.split('\n').length > 8;

  return (
    <div className="pt-4 md:pt-6 px-4 md:px-6 pb-4 md:pb-6">
      <div className="max-w-7xl mx-auto">
        <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-xl lg:rounded-2xl p-4 md:p-6 lg:p-8">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between mb-6 md:mb-8 gap-4">
            <div className="flex-1">
              <h2 className="text-xl md:text-2xl lg:text-3xl font-semibold text-white mb-3 flex items-center">
                <svg className="w-7 h-7 md:w-8 md:h-8 mr-3 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                System Instructions
              </h2>
              <p className="text-gray-400 text-sm md:text-base">
                Add these instructions to your AI assistant to help it use MemCP more efficiently. This significantly improves memory management and reduces unnecessary API calls.
              </p>
            </div>

            <button
              onClick={handleCopyPrompt}
              className="px-6 py-3 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/50 text-purple-400 rounded-lg transition-all text-sm md:text-base font-medium shrink-0 flex items-center gap-2 self-start"
            >
              {copyFeedback ? (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Copied!
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Copy Instructions
                </>
              )}
            </button>
          </div>

          <div className="space-y-6">
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <svg className="w-6 h-6 text-blue-400 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="text-sm text-blue-300">
                  <p className="font-medium mb-2">Where to add these instructions:</p>
                  <ul className="space-y-1.5 text-blue-300/90">
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 font-bold mt-0.5">•</span>
                      <span><strong>ChatGPT:</strong> Settings → Personalization → Custom Instructions → "How would you like ChatGPT to respond?"</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 font-bold mt-0.5">•</span>
                      <span><strong>Claude Desktop:</strong> Not directly supported. Use MCP configuration files instead.</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 font-bold mt-0.5">•</span>
                      <span><strong>Cursor:</strong> Cursor Settings → Rules for AI → Add these instructions</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 font-bold mt-0.5">•</span>
                      <span><strong>Other clients:</strong> Look for "System Prompt", "Custom Instructions", or "AI Behavior" settings</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="bg-gray-800/50 border border-gray-700 rounded-xl overflow-hidden">
              <div className="flex items-center justify-between p-4 bg-gray-800/70 border-b border-gray-700">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
                    <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
                    <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
                  </div>
                  <span className="text-xs text-gray-400 ml-2 font-mono">system_instructions.md</span>
                </div>
                {isLongPrompt && (
                  <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="text-xs text-gray-400 hover:text-gray-300 transition-colors flex items-center gap-1"
                  >
                    {isExpanded ? (
                      <>
                        <span>Collapse</span>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                        </svg>
                      </>
                    ) : (
                      <>
                        <span>Expand</span>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </>
                    )}
                  </button>
                )}
              </div>

              <div className="relative">
                <pre className={`bg-gray-900 p-4 md:p-6 overflow-x-auto text-sm md:text-base ${!isExpanded && isLongPrompt ? 'max-h-64' : ''}`}>
                  <code className="text-gray-300 font-mono whitespace-pre">
                    {isExpanded || !isLongPrompt ? MEMCP_SYSTEM_PROMPT : previewLines}
                  </code>
                </pre>

                {!isExpanded && isLongPrompt && (
                  <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-gray-900 to-transparent pointer-events-none"></div>
                )}
              </div>
            </div>

            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <svg className="w-6 h-6 text-green-400 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="text-sm text-green-300">
                  <p className="font-medium mb-2">Why add system instructions?</p>
                  <ul className="space-y-1.5 text-green-300/90">
                    <li className="flex items-start gap-2">
                      <span className="text-green-400 font-bold mt-0.5">✓</span>
                      <span>Prevents redundant memory operations and API calls</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-green-400 font-bold mt-0.5">✓</span>
                      <span>Ensures proper context retrieval at the start of conversations</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-green-400 font-bold mt-0.5">✓</span>
                      <span>Helps AI decide when to remember vs. when to search memories</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-green-400 font-bold mt-0.5">✓</span>
                      <span>Improves overall conversation quality with better context awareness</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
