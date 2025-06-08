import { type FC, useState } from "react";
import { Eye, EyeOff, Lock, User, Mail } from "lucide-react";
import { registerUser } from "../../api";
import type { UserCreate } from "../../types";

type RegisterFormProps = {
    onSubmit?: (data: { email: string; username: string; password: string }) => void;
    onSuccess?: (user: any) => void;
    onError?: (error: string) => void;
};

export const RegisterForm: FC<RegisterFormProps> = ({ onSubmit, onSuccess, onError }) => {
    const [formData, setFormData] = useState({
        email: "",
        username: "",
        password: "",
        confirmPassword: "",
    });
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [errors, setErrors] = useState<{ 
        email?: string; 
        username?: string; 
        password?: string; 
        confirmPassword?: string; 
        general?: string;
    }>({});
    const [isLoading, setIsLoading] = useState(false);

    const validateEmail = (email: string) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    };

    const validateForm = () => {
        const newErrors: { 
            email?: string; 
            username?: string; 
            password?: string; 
            confirmPassword?: string; 
            general?: string;
        } = {};

        // Email validation
        if (!formData.email.trim()) {
            newErrors.email = "Email is required";
        } else if (!validateEmail(formData.email)) {
            newErrors.email = "Please enter a valid email address";
        }

        // Username validation
        if (!formData.username.trim()) {
            newErrors.username = "Username is required";
        } else if (formData.username.length < 3) {
            newErrors.username = "Username must be at least 3 characters";
        } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
            newErrors.username = "Username can only contain letters, numbers, and underscores";
        }

        // Password validation
        if (!formData.password) {
            newErrors.password = "Password is required";
        } else if (formData.password.length < 6) {
            newErrors.password = "Password must be at least 8 characters";
        }

        // Confirm password validation
        if (!formData.confirmPassword) {
            newErrors.confirmPassword = "Please confirm your password";
        } else if (formData.password !== formData.confirmPassword) {
            newErrors.confirmPassword = "Passwords do not match";
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
            // Create user data for API call
            const userData: UserCreate = {
                email: formData.email,
                username: formData.username,
                password: formData.password,
                is_active: true,
                is_superuser: false
            };
            
            const user = await registerUser(userData);
            
            // Call the onSubmit callback if provided (for backward compatibility)
            if (onSubmit) {
                onSubmit({
                    email: formData.email,
                    username: formData.username,
                    password: formData.password
                });
            }
            
            console.log("Registration successful:", user);
            
            // Call the onSuccess callback with the user
            if (onSuccess) {
                onSuccess(user);
            } else {
                // Default behavior: redirect to login page
                console.log("Redirecting to login page...");
                window.location.href = '/login';
            }
        } catch (error) {
            console.error("Registration error:", error);
            const errorMessage = error instanceof Error ? error.message : "Registration failed. Please try again.";
            
            setErrors(prev => ({ ...prev, general: errorMessage }));
            
            if (onError) {
                onError(errorMessage);
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleInputChange = (field: "email" | "username" | "password" | "confirmPassword") => (
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

        // Also clear confirm password error if password changes
        if (field === "password" && errors.confirmPassword) {
            setErrors(prev => ({
                ...prev,
                confirmPassword: undefined
            }));
        }
    };

    return (
        <div className="mx-auto max-w-md w-full">
            <form onSubmit={handleSubmit} className="space-y-6">
                {/* Email Field */}
                <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                        Email Address
                    </label>
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Mail className="h-5 w-5 text-gray-400" />
                        </div>
                        <input
                            id="email"
                            name="email"
                            type="email"
                            autoComplete="email"
                            required
                            value={formData.email}
                            onChange={handleInputChange("email")}
                            className={`
                                w-full pl-10 pr-4 py-3 
                                bg-gray-800/50 border rounded-lg
                                text-white placeholder-gray-400
                                focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent
                                transition-all duration-200
                                ${errors.email ? 'border-red-500' : 'border-gray-600 hover:border-gray-500'}
                            `}
                            placeholder="Enter your email"
                        />
                    </div>
                    {errors.email && (
                        <p className="mt-1 text-sm text-red-400" role="alert">
                            {errors.email}
                        </p>
                    )}
                </div>

                {/* Username Field */}
                <div>
                    <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-2">
                        Username
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
                            placeholder="Choose a username"
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
                            autoComplete="new-password"
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
                            placeholder="Create a strong password"
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

                {/* Confirm Password Field */}
                <div>
                    <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-300 mb-2">
                        Confirm Password
                    </label>
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Lock className="h-5 w-5 text-gray-400" />
                        </div>
                        <input
                            id="confirmPassword"
                            name="confirmPassword"
                            type={showConfirmPassword ? "text" : "password"}
                            autoComplete="new-password"
                            required
                            value={formData.confirmPassword}
                            onChange={handleInputChange("confirmPassword")}
                            className={`
                                w-full pl-10 pr-12 py-3 
                                bg-gray-800/50 border rounded-lg
                                text-white placeholder-gray-400
                                focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent
                                transition-all duration-200
                                ${errors.confirmPassword ? 'border-red-500' : 'border-gray-600 hover:border-gray-500'}
                            `}
                            placeholder="Confirm your password"
                        />
                        <button
                            type="button"
                            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                            className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-300 transition-colors"
                            aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                        >
                            {showConfirmPassword ? (
                                <EyeOff className="h-5 w-5" />
                            ) : (
                                <Eye className="h-5 w-5" />
                            )}
                        </button>
                    </div>
                    {errors.confirmPassword && (
                        <p className="mt-1 text-sm text-red-400" role="alert">
                            {errors.confirmPassword}
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
                            Creating account...
                        </div>
                    ) : (
                        "Create Account"
                    )}
                </button>

                {/* Terms and Conditions */}
                <div className="text-center">
                    <p className="text-xs text-gray-400">
                        By creating an account, you agree to our{" "}
                        <a
                            href="/terms"
                            className="text-purple-400 hover:text-purple-300 transition-colors"
                        >
                            Terms of Service
                        </a>{" "}
                        and{" "}
                        <a
                            href="/privacy"
                            className="text-purple-400 hover:text-purple-300 transition-colors"
                        >
                            Privacy Policy
                        </a>
                    </p>
                </div>
            </form>
        </div>
    );
}; 