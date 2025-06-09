import React from 'react';

interface MemoryDetailPanelProps {
  selectedMemory?: {
    id: string;
    title: string;
    content: string;
    tags: string[];
    createdAt: string;
    updatedAt: string;
  };
  onEdit?: () => void;
  onDelete?: () => void;
}

export const MemoryDetailPanel: React.FC<MemoryDetailPanelProps> = ({ selectedMemory, onEdit, onDelete }) => {
  if (!selectedMemory) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="w-20 h-20 mx-auto mb-6 bg-gray-800/50 rounded-2xl flex items-center justify-center">
            <svg className="w-10 h-10 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} 
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <p className="text-gray-500 text-lg font-medium">Select a memory to view details</p>
          <p className="text-gray-600 text-sm mt-2">Click on any node in the mind map</p>
        </div>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 24) {
      return `Today, ${date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit', 
        hour12: true 
      })}`;
    } else if (diffInHours < 48) {
      return `Yesterday, ${date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit', 
        hour12: true 
      })}`;
    } else {
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    }
  };

  return (
    <div className="h-full flex flex-col p-8">
      {/* Memory Title with Actions */}
      <div className="mb-8">
        <div className="flex items-start justify-between mb-4">
          <h2 className="text-3xl font-semibold text-white leading-tight flex-1">
            {selectedMemory.title}
          </h2>
          <div className="flex items-center space-x-2 ml-4">
            {onEdit && (
              <button
                onClick={onEdit}
                className="p-2 bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/50 rounded-lg transition-all group"
                title="Edit Memory"
              >
                <svg className="w-4 h-4 text-emerald-400 group-hover:text-emerald-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
            )}
            {onDelete && (
              <button
                onClick={onDelete}
                className="p-2 bg-red-600/20 hover:bg-red-600/30 border border-red-500/50 rounded-lg transition-all group"
                title="Delete Memory"
              >
                <svg className="w-4 h-4 text-red-400 group-hover:text-red-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Memory Content */}
      <div className="flex-1 space-y-6 overflow-y-auto">
        {/* Full Content Section */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">Full Content</h3>
          <div className="bg-gray-800/30 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50">
            <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">
              {selectedMemory.content || "No detailed content available for this memory."}
            </p>
          </div>
        </div>

        {/* Tags Section */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">Tags</h3>
          <div className="flex flex-wrap gap-2">
            {selectedMemory.tags && selectedMemory.tags.length > 0 ? (
              selectedMemory.tags.map((tag, index) => (
                <span
                  key={index}
                  className="px-4 py-2 bg-gray-800/50 backdrop-blur-sm text-gray-300 rounded-full text-sm font-medium border border-gray-700/50 hover:border-gray-600 transition-colors"
                >
                  {tag}
                </span>
              ))
            ) : (
              <span className="text-gray-500 text-sm">No tags assigned</span>
            )}
          </div>
        </div>

        {/* Timestamps Section */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">Timeline</h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between py-2">
              <span className="text-gray-500 text-sm">Created</span>
              <span className="text-gray-300 text-sm font-medium">
                {formatDate(selectedMemory.createdAt)}
              </span>
            </div>
            <div className="h-px bg-gray-800"></div>
            <div className="flex items-center justify-between py-2">
              <span className="text-gray-500 text-sm">Last updated</span>
              <span className="text-gray-300 text-sm font-medium">
                {formatDate(selectedMemory.updatedAt)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Timeline View Button */}
      <div className="mt-8">
        <button className="w-full group relative overflow-hidden rounded-xl transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]">
          {/* Gradient Border Effect */}
          <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 opacity-80 blur-sm group-hover:opacity-100 transition-opacity"></div>
          
          {/* Button Background */}
          <div className="relative bg-gray-900 rounded-xl border border-gray-700 group-hover:border-transparent transition-colors">
            <div className="px-6 py-4 flex items-center justify-center space-x-3">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-white font-medium text-lg">Open in Timeline View</span>
            </div>
          </div>
        </button>
      </div>
    </div>
  );
};