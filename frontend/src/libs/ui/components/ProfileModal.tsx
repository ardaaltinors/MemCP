import React, { useState, useEffect } from 'react';
import { X, User, Calendar, Hash } from 'lucide-react';
import { getProcessedUserProfile } from '@libs/api';
import { authUtils } from '@libs/utils/auth';
import type { ProcessedUserProfile } from '@libs/types';

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ProfileModal({ isOpen, onClose }: ProfileModalProps) {
  const [profile, setProfile] = useState<ProcessedUserProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchProfile();
    }
  }, [isOpen]);

  const fetchProfile = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = authUtils.getToken();
      if (!token) throw new Error('No authentication token');
      
      const data = await getProcessedUserProfile(token);
      setProfile(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const renderValue = (value: any): string | React.ReactElement => {
    if (value === null || value === undefined) {
      return 'Not set';
    }
    
    if (typeof value === 'object' && !Array.isArray(value)) {
      // For nested objects, render them as a formatted list
      return (
        <div className="space-y-1">
          {Object.entries(value).map(([k, v]) => (
            <div key={k} className="text-sm">
              <span className="text-gray-400">{k.replace(/_/g, ' ')}:</span>{' '}
              <span className="text-gray-200">{String(v)}</span>
            </div>
          ))}
        </div>
      );
    }
    
    if (Array.isArray(value)) {
      return value.join(', ');
    }
    
    return String(value);
  };

  const renderMetadata = (metadata: Record<string, any>) => {
    return Object.entries(metadata).map(([key, value]) => {
      if (key === 'profile_id' && value === null) return null;
      
      const renderedValue = renderValue(value);
      
      return (
        <div key={key} className="flex justify-between items-start gap-4 py-2">
          <span className="text-gray-400 capitalize">
            {key.replace(/_/g, ' ')}:
          </span>
          <div className="text-gray-200 text-right">
            {renderedValue}
          </div>
        </div>
      );
    }).filter(Boolean);
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gray-900 border border-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-gray-800">
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <User className="w-5 h-5" />
            User Profile
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          )}

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-red-400">
              {error}
            </div>
          )}

          {profile && !loading && (
            <div className="space-y-6">
              {/* Profile ID and User ID */}
              <div className="bg-gray-800/50 rounded-lg p-4 space-y-3">
                <div className="flex items-center gap-2 text-gray-300">
                  <Hash className="w-4 h-4" />
                  <span className="text-sm">Profile ID:</span>
                  <span className="font-mono text-xs text-gray-400">{profile.id}</span>
                </div>
                <div className="flex items-center gap-2 text-gray-300">
                  <User className="w-4 h-4" />
                  <span className="text-sm">User ID:</span>
                  <span className="font-mono text-xs text-gray-400">{profile.user_id}</span>
                </div>
              </div>

              {/* Summary */}
              {profile.summary_text && (
                <div className="space-y-2">
                  <h3 className="text-lg font-medium text-white">Summary</h3>
                  <div className="bg-gray-800/30 rounded-lg p-4">
                    <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">
                      {profile.summary_text}
                    </p>
                  </div>
                </div>
              )}

              {/* Metadata */}
              {profile.metadata_json && Object.keys(profile.metadata_json).length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-lg font-medium text-white">Profile Information</h3>
                  <div className="bg-gray-800/30 rounded-lg p-4 divide-y divide-gray-700">
                    {renderMetadata(profile.metadata_json)}
                  </div>
                </div>
              )}

              {/* Timestamps */}
              <div className="bg-gray-800/30 rounded-lg p-4 space-y-2">
                <div className="flex items-center gap-2 text-gray-400 text-sm">
                  <Calendar className="w-4 h-4" />
                  <span>Created:</span>
                  <span className="text-gray-300">{formatDate(profile.created_at)}</span>
                </div>
                <div className="flex items-center gap-2 text-gray-400 text-sm">
                  <Calendar className="w-4 h-4" />
                  <span>Last Updated:</span>
                  <span className="text-gray-300">{formatDate(profile.updated_at)}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}