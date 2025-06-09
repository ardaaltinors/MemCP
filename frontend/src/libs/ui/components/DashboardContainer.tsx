import React, { useState, useEffect } from 'react';
import { MemoryGraphDashboard } from './MemoryGraphDashboard';
import { MemoryDetailPanel } from './MemoryDetailPanel';
import { ApiKeyManager } from './ApiKeyManager';
import { ClientSelector } from './ClientSelector';
import { createMemory, updateMemory, deleteMemory } from '@libs/api';
import type { CreateMemoryRequest, UpdateMemoryRequest } from '@libs/types';
import { authUtils } from '@libs/utils/auth';

// Update Memory Modal Component
const UpdateMemoryModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (id: string, memory: UpdateMemoryRequest) => Promise<void>;
  memory?: MemoryData;
}> = ({ isOpen, onClose, onSubmit, memory }) => {
  const [content, setContent] = useState('');
  const [tags, setTags] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Update form when memory changes
  React.useEffect(() => {
    if (memory) {
      setContent(memory.content);
      setTags(memory.tags.join(', '));
    }
  }, [memory]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!memory || !content.trim()) return;

    setIsSubmitting(true);
    try {
      const tagArray = tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0);
      await onSubmit(memory.id, { content: content.trim(), tags: tagArray });
      onClose();
    } catch (error) {
      console.error('Failed to update memory:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen || !memory) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-gray-900 rounded-2xl border border-gray-800 p-6 max-w-lg w-full">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold text-white">Update Memory</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Content</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Enter memory content..."
              className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 outline-none transition-colors min-h-[120px]"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Tags (comma-separated)</label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="tag1, tag2, tag3..."
              className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 outline-none transition-colors"
            />
          </div>
          
          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!content.trim() || isSubmitting}
              className="px-6 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-medium hover:scale-105 disabled:opacity-50 disabled:transform-none transition-all"
            >
              {isSubmitting ? 'Updating...' : 'Update Memory'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Delete Confirmation Modal Component
const DeleteConfirmModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  memoryTitle?: string;
}> = ({ isOpen, onClose, onConfirm, memoryTitle }) => {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleConfirm = async () => {
    setIsDeleting(true);
    try {
      await onConfirm();
      onClose();
    } catch (error) {
      console.error('Failed to delete memory:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-gray-900 rounded-2xl border border-gray-800 p-6 max-w-md w-full">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold text-white">Delete Memory</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="mb-6">
          <div className="w-16 h-16 mx-auto mb-4 bg-red-500/20 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </div>
          <p className="text-gray-300 text-center mb-2">
            Are you sure you want to delete this memory?
          </p>
          {memoryTitle && (
            <p className="text-gray-500 text-center text-sm font-medium">
              "{memoryTitle}"
            </p>
          )}
          <p className="text-red-400 text-center text-sm mt-3">
            This action cannot be undone.
          </p>
        </div>
        
        <div className="flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={isDeleting}
            className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium disabled:opacity-50 transition-all"
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  );
};

interface MemoryData {
  id: string;
  title: string;
  content: string;
  tags: string[];
  createdAt: string;
  updatedAt: string;
}

export const DashboardContainer: React.FC = () => {
  const [selectedMemory, setSelectedMemory] = useState<MemoryData | undefined>(undefined);
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const [showClientModal, setShowClientModal] = useState(false);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const handleNodeSelect = (memory: MemoryData) => {
    setSelectedMemory(memory);
  };

  const handleMemoryCreate = async (memory: CreateMemoryRequest) => {
    try {
      const token = authUtils.getToken();
      if (!token) throw new Error('Not authenticated');
      
      await createMemory(token, memory);
      // The graph will refresh automatically
    } catch (error) {
      console.error('Failed to create memory:', error);
      throw error;
    }
  };

  const handleMemoryUpdate = async (id: string, memory: UpdateMemoryRequest) => {
    try {
      const token = authUtils.getToken();
      if (!token) throw new Error('Not authenticated');
      
      await updateMemory(token, id, memory);
      // Update selected memory if it's the one being updated
      if (selectedMemory?.id === id) {
        setSelectedMemory({
          ...selectedMemory,
          content: memory.content || selectedMemory.content,
          tags: memory.tags || selectedMemory.tags,
          updatedAt: new Date().toISOString(),
        });
      }
    } catch (error) {
      console.error('Failed to update memory:', error);
      throw error;
    }
  };

  const handleMemoryUpdateFromPanel = async (id: string, memory: UpdateMemoryRequest) => {
    await handleMemoryUpdate(id, memory);
    setShowUpdateModal(false);
  };

  const handleMemoryDeleteFromPanel = async () => {
    if (selectedMemory) {
      await handleMemoryDelete(selectedMemory.id);
      setShowDeleteModal(false);
    }
  };

  const handleMemoryDelete = async (id: string) => {
    try {
      const token = authUtils.getToken();
      if (!token) throw new Error('Not authenticated');
      
      await deleteMemory(token, id);
      // Clear selection if deleted memory was selected
      if (selectedMemory?.id === id) {
        setSelectedMemory(undefined);
      }
    } catch (error) {
      console.error('Failed to delete memory:', error);
      throw error;
    }
  };

  // Set up event listeners for header buttons
  useEffect(() => {
    const handleApiKeyClick = () => setShowApiKeyModal(true);
    const handleClientClick = () => setShowClientModal(true);

    // Add event listeners
    window.addEventListener('show-api-key-modal', handleApiKeyClick);
    window.addEventListener('show-client-modal', handleClientClick);

    // Set up button click handlers after component mounts
    const setupButtons = () => {
      const apiKeyButton = document.querySelector('button[aria-label="API Key"]');
      const settingsButton = document.querySelector('button[aria-label="Settings"]');

      if (apiKeyButton) {
        apiKeyButton.addEventListener('click', handleApiKeyClick);
      }

      if (settingsButton) {
        settingsButton.addEventListener('click', handleClientClick);
      }
    };

    // Delay to ensure DOM is ready
    setTimeout(setupButtons, 100);

    return () => {
      window.removeEventListener('show-api-key-modal', handleApiKeyClick);
      window.removeEventListener('show-client-modal', handleClientClick);
    };
  }, []);

  return (
    <>
      {/* Main Content Area */}
      <div className="flex h-[calc(100vh-6rem)]">
        {/* Left Section: Interactive Memory Map (60%) */}
        <div className="w-[60%] h-full border-r border-gray-800/50">
          <div className="h-full relative">
            <MemoryGraphDashboard 
              onNodeSelect={handleNodeSelect}
              onMemoryCreate={handleMemoryCreate}
              onMemoryUpdate={handleMemoryUpdate}
              onMemoryDelete={handleMemoryDelete}
            />
          </div>
        </div>

        {/* Right Section: Memory Detail Panel (40%) */}
        <div className="w-[40%] h-full bg-[#0D0D1A]">
          <div className="h-full">
            <MemoryDetailPanel 
              selectedMemory={selectedMemory} 
              onEdit={() => setShowUpdateModal(true)}
              onDelete={() => setShowDeleteModal(true)}
            />
          </div>
        </div>
      </div>

      {/* API Key Modal */}
      {showApiKeyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-gray-900 rounded-2xl border border-gray-800 p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-semibold text-white">API Key Management</h2>
              <button
                onClick={() => setShowApiKeyModal(false)}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              >
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <ApiKeyManager />
          </div>
        </div>
      )}

      {/* Client Selector Modal */}
      {showClientModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-gray-900 rounded-2xl border border-gray-800 p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-semibold text-white">MCP Client Configuration</h2>
              <button
                onClick={() => setShowClientModal(false)}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              >
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <ClientSelector />
          </div>
        </div>
      )}

      {/* Update Memory Modal */}
      <UpdateMemoryModal
        isOpen={showUpdateModal}
        onClose={() => setShowUpdateModal(false)}
        onSubmit={handleMemoryUpdateFromPanel}
        memory={selectedMemory}
      />

      {/* Delete Memory Modal */}
      <DeleteConfirmModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={handleMemoryDeleteFromPanel}
        memoryTitle={selectedMemory?.title}
      />
    </>
  );
};