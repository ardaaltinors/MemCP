import React, { useState } from 'react';
import { changePassword, deleteAllMemories } from '@libs/api';
import { authUtils } from '@libs/utils/auth';
import { Eye, EyeOff, Lock, Trash2, AlertTriangle } from 'lucide-react';

export const SettingsContainer: React.FC = () => {
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [isDeletingMemories, setIsDeletingMemories] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  
  const [passwordForm, setPasswordForm] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  
  const [showPasswords, setShowPasswords] = useState({
    old: false,
    new: false,
    confirm: false
  });
  
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [success, setSuccess] = useState<{ [key: string]: string }>({});

  const validatePasswordForm = () => {
    const newErrors: { [key: string]: string } = {};
    
    if (!passwordForm.oldPassword) {
      newErrors.oldPassword = 'Current password is required';
    }
    
    if (!passwordForm.newPassword) {
      newErrors.newPassword = 'New password is required';
    } else if (passwordForm.newPassword.length < 6) {
      newErrors.newPassword = 'Password must be at least 6 characters';
    }
    
    if (!passwordForm.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your new password';
    } else if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validatePasswordForm()) {
      return;
    }
    
    setIsChangingPassword(true);
    setErrors({});
    setSuccess({});
    
    try {
      const token = authUtils.getToken();
      if (!token) throw new Error('Not authenticated');
      
      await changePassword(token, passwordForm.oldPassword, passwordForm.newPassword);
      
      setSuccess({ password: 'Password changed successfully!' });
      setPasswordForm({ oldPassword: '', newPassword: '', confirmPassword: '' });
      
      // Clear success message after 5 seconds
      setTimeout(() => setSuccess({}), 5000);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to change password';
      setErrors({ password: message });
    } finally {
      setIsChangingPassword(false);
    }
  };
  
  const handleDeleteAllMemories = async () => {
    setIsDeletingMemories(true);
    setErrors({});
    setSuccess({});
    
    try {
      const token = authUtils.getToken();
      if (!token) throw new Error('Not authenticated');
      
      await deleteAllMemories(token);
      
      setSuccess({ memories: 'All memories deleted successfully!' });
      setShowDeleteConfirm(false);
      
      // Clear success message after 5 seconds
      setTimeout(() => setSuccess({}), 5000);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete memories';
      setErrors({ memories: message });
    } finally {
      setIsDeletingMemories(false);
    }
  };

  return (
    <div className="pt-20 md:pt-24 lg:pt-28 px-4 md:px-6 pb-12">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Password Change Section */}
        <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6 md:p-8">
          <h2 className="text-xl md:text-2xl font-semibold text-white mb-6">Change Password</h2>
          
          <form onSubmit={handlePasswordChange} className="space-y-4">
            {/* Current Password */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Current Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type={showPasswords.old ? "text" : "password"}
                  value={passwordForm.oldPassword}
                  onChange={(e) => setPasswordForm({ ...passwordForm, oldPassword: e.target.value })}
                  className="w-full pl-10 pr-12 py-3 bg-gray-800/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                  placeholder="Enter current password"
                />
                <button
                  type="button"
                  onClick={() => setShowPasswords({ ...showPasswords, old: !showPasswords.old })}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-300"
                >
                  {showPasswords.old ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              {errors.oldPassword && (
                <p className="mt-1 text-sm text-red-400">{errors.oldPassword}</p>
              )}
            </div>
            
            {/* New Password */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                New Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type={showPasswords.new ? "text" : "password"}
                  value={passwordForm.newPassword}
                  onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                  className="w-full pl-10 pr-12 py-3 bg-gray-800/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                  placeholder="Enter new password"
                />
                <button
                  type="button"
                  onClick={() => setShowPasswords({ ...showPasswords, new: !showPasswords.new })}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-300"
                >
                  {showPasswords.new ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              {errors.newPassword && (
                <p className="mt-1 text-sm text-red-400">{errors.newPassword}</p>
              )}
            </div>
            
            {/* Confirm New Password */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Confirm New Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type={showPasswords.confirm ? "text" : "password"}
                  value={passwordForm.confirmPassword}
                  onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                  className="w-full pl-10 pr-12 py-3 bg-gray-800/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                  placeholder="Confirm new password"
                />
                <button
                  type="button"
                  onClick={() => setShowPasswords({ ...showPasswords, confirm: !showPasswords.confirm })}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-300"
                >
                  {showPasswords.confirm ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className="mt-1 text-sm text-red-400">{errors.confirmPassword}</p>
              )}
            </div>
            
            {/* Error/Success Messages */}
            {errors.password && (
              <div className="p-3 rounded-lg bg-red-900/20 border border-red-500/30">
                <p className="text-sm text-red-400">{errors.password}</p>
              </div>
            )}
            
            {success.password && (
              <div className="p-3 rounded-lg bg-green-900/20 border border-green-500/30">
                <p className="text-sm text-green-400">{success.password}</p>
              </div>
            )}
            
            {/* Submit Button */}
            <button
              type="submit"
              disabled={isChangingPassword}
              className="w-full py-3 px-4 rounded-lg font-semibold text-white bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-700 hover:to-blue-600 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isChangingPassword ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Changing Password...
                </div>
              ) : (
                "Change Password"
              )}
            </button>
          </form>
        </div>

        {/* Delete All Memories Section */}
        <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6 md:p-8">
          <h2 className="text-xl md:text-2xl font-semibold text-white mb-6">Data Management</h2>
          
          <div className="space-y-6">
            <div className="bg-red-900/10 border border-red-900/30 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="h-5 w-5 text-red-400 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-red-400 mb-2">Delete All Memories</h3>
                  <p className="text-sm text-gray-300 mb-4">
                    This action will permanently delete all your memories, facts, and relationships. This cannot be undone.
                  </p>
                  
                  {!showDeleteConfirm ? (
                    <button
                      onClick={() => {
                        setShowDeleteConfirm(true);
                        setDeleteConfirmText('');
                      }}
                      className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors flex items-center space-x-2"
                    >
                      <Trash2 className="h-4 w-4" />
                      <span>Delete All Memories</span>
                    </button>
                  ) : (
                    <div className="space-y-3">
                      <p className="text-sm font-medium text-red-400">
                        Are you absolutely sure? Type "DELETE" to confirm:
                      </p>
                      <div className="flex items-center space-x-3">
                        <input
                          type="text"
                          value={deleteConfirmText}
                          placeholder="Type DELETE to confirm"
                          className={`px-3 py-2 bg-gray-800/50 border rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500 ${
                            deleteConfirmText === 'DELETE' ? 'border-green-500' : 'border-gray-600'
                          }`}
                          onChange={(e) => setDeleteConfirmText(e.target.value)}
                        />
                        <button
                          onClick={handleDeleteAllMemories}
                          disabled={isDeletingMemories || deleteConfirmText !== 'DELETE'}
                          className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {isDeletingMemories ? (
                            <div className="flex items-center">
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                              Deleting...
                            </div>
                          ) : (
                            "Confirm Delete"
                          )}
                        </button>
                        <button
                          onClick={() => {
                            setShowDeleteConfirm(false);
                            setDeleteConfirmText('');
                          }}
                          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                  
                  {/* Error/Success Messages */}
                  {errors.memories && (
                    <div className="mt-4 p-3 rounded-lg bg-red-900/20 border border-red-500/30">
                      <p className="text-sm text-red-400">{errors.memories}</p>
                    </div>
                  )}
                  
                  {success.memories && (
                    <div className="mt-4 p-3 rounded-lg bg-green-900/20 border border-green-500/30">
                      <p className="text-sm text-green-400">{success.memories}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};