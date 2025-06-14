import { type FC, useState } from "react";
import { Eye, EyeOff, Lock, User } from "lucide-react";
import { loginUser, getApiKey } from "../../api";
import { authUtils } from "../../utils/auth";
import type { Token } from "../../types";

type LoginFormProps = {
    onSubmit?: (data: { username: string; password: string }) => void;
    onSuccess?: (token: Token) => void;
    onError?: (error: string) => void;
};

export const LoginForm: FC<LoginFormProps> = ({ onSubmit, onSuccess, onError }) => {
    const [formData, setFormData] = useState({
        username: "",
        password: "",
    });
    const [showPassword, setShowPassword] = useState(false);
    const [errors, setErrors] = useState<{ username?: string; password?: string; general?: string }>({});
    const [isLoading, setIsLoading] = useState(false);

    const validateForm = () => {
        const newErrors: { username?: string; password?: string; general?: string } = {};

        if (!formData.username.trim()) {
            newErrors.username = "Username or email is required";
        } else {
            // Check if it's an email or username
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            const usernameRegex = /^[a-zA-Z0-9_-]+$/;
            
            if (!emailRegex.test(formData.username) && !usernameRegex.test(formData.username)) {
                newErrors.username = "Please enter a valid username or email";
            }
        }

        if (!formData.password) {
            newErrors.password = "Password is required";
        } else if (formData.password.length < 6) {
            newErrors.password = "Password must be at least 6 characters";
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!validateForm()) {
            return;
        }

        setIsLoading(true);
        // Clear any previous general errors
        setErrors(prev => ({ ...prev, general: undefined }));
        
        try {
            // Create URLSearchParams for the login request
            const credentials = new URLSearchParams();
            credentials.append('username', formData.username);
            credentials.append('password', formData.password);
            
            const token = await loginUser(credentials);
            
            // Call the onSubmit callback if provided (for backward compatibility)
            if (onSubmit) {
                onSubmit(formData);
            }
            
            // Store token using authUtils
            authUtils.storeToken(token);
            
            console.log("Login successful:", token);
            console.log("Token stored in localStorage using authUtils");
            
            // Call the onSuccess callback with the token if provided
            if (onSuccess) {
                console.log("Calling onSuccess callback...");
                onSuccess(token);
            }
            
            // Check if user has API key
            try {
                console.log("Checking for existing API key...");
                const apiKeyResponse = await getApiKey(token.access_token);
                
                // If API key exists, redirect to dashboard
                if (apiKeyResponse.api_key) {
                    console.log("User has API key, redirecting to dashboard...");
                    window.location.href = '/dashboard';
                } else {
                    console.log("No API key found, redirecting to credentials...");
                    window.location.href = '/credentials';
                }
            } catch (apiKeyError) {
                // If fetching API key fails (404 or other error), redirect to credentials
                console.log("Error fetching API key or no API key exists, redirecting to credentials...");
                window.location.href = '/credentials';
            }
        } catch (error) {
            console.error("Login error:", error);
            const errorMessage = error instanceof Error ? error.message : "Login failed. Please try again.";
            
            setErrors(prev => ({ ...prev, general: errorMessage }));
            
            if (onError) {
                onError(errorMessage);
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleInputChange = (field: "username" | "password") => (
        e: React.ChangeEvent<HTMLInputElement>
    ) => {
        setFormData(prev => ({
            ...prev,
            [field]: e.target.value
        }));
        
        // Clear error when user starts typing
        if (errors[field]) {
            setErrors(prev => ({
                ...prev,
                [field]: undefined
            }));
        }
    };

    return (
        <div className="mx-auto max-w-md w-full">
            <form onSubmit={handleSubmit} className="space-y-6">
                {/* Username Field */}
                <div>
                    <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-2">
                        Username or Email
                    </label>
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <User className="h-5 w-5 text-gray-400" />
                        </div>
                        <input
                            id="username"
                            name="username"
                            type="text"
                            autoComplete="username"
                            required
                            value={formData.username}
                            onChange={handleInputChange("username")}
                            className={`
                                w-full pl-10 pr-4 py-3 
                                bg-gray-800/50 border rounded-lg
                                text-white placeholder-gray-400
                                focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent
                                transition-all duration-200
                                ${errors.username ? 'border-red-500' : 'border-gray-600 hover:border-gray-500'}
                            `}
                            placeholder="Enter your username or email"
                        />
                    </div>
                    {errors.username && (
                        <p className="mt-1 text-sm text-red-400" role="alert">
                            {errors.username}
                        </p>
                    )}
                </div>

                {/* Password Field */}
                <div>
                    <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
                        Password
                    </label>
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Lock className="h-5 w-5 text-gray-400" />
                        </div>
                        <input
                            id="password"
                            name="password"
                            type={showPassword ? "text" : "password"}
                            autoComplete="current-password"
                            required
                            value={formData.password}
                            onChange={handleInputChange("password")}
                            className={`
                                w-full pl-10 pr-12 py-3 
                                bg-gray-800/50 border rounded-lg
                                text-white placeholder-gray-400
                                focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent
                                transition-all duration-200
                                ${errors.password ? 'border-red-500' : 'border-gray-600 hover:border-gray-500'}
                            `}
                            placeholder="Enter your password"
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-300 transition-colors"
                            aria-label={showPassword ? "Hide password" : "Show password"}
                        >
                            {showPassword ? (
                                <EyeOff className="h-5 w-5" />
                            ) : (
                                <Eye className="h-5 w-5" />
                            )}
                        </button>
                    </div>
                    {errors.password && (
                        <p className="mt-1 text-sm text-red-400" role="alert">
                            {errors.password}
                        </p>
                    )}
                </div>

                {/* General Error Display */}
                {errors.general && (
                    <div className="p-3 rounded-lg bg-red-900/20 border border-red-500/30">
                        <p className="text-sm text-red-400 text-center" role="alert">
                            {errors.general}
                        </p>
                    </div>
                )}

                {/* Submit Button */}
                <button
                    type="submit"
                    disabled={isLoading}
                    className={`
                        w-full py-3 px-4 rounded-lg font-semibold text-white
                        bg-gradient-to-r from-purple-600 to-blue-500
                        hover:from-purple-700 hover:to-blue-600
                        focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-gray-900
                        disabled:opacity-50 disabled:cursor-not-allowed
                        transition-all duration-200
                        ${isLoading ? 'cursor-wait' : ''}
                    `}
                >
                    {isLoading ? (
                        <div className="flex items-center justify-center">
                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                            Signing in...
                        </div>
                    ) : (
                        "Sign In"
                    )}
                </button>

                {/* Additional Links */}
                <div className="text-center">
                    <a
                        href="#"
                        className="text-sm text-gray-400 hover:text-gray-300 transition-colors"
                    >
                        Forgot your password?
                    </a>
                </div>
            </form>
        </div>
    );
}; 