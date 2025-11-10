import type { UserCreate, User, Token, ApiKeyResponse, CreateApiKeyResponse, RevokeApiKeyResponse, MemoryGraphResponse, Memory, CreateMemoryRequest, UpdateMemoryRequest, DeleteMemoryResponse, ProcessedUserProfile, DeleteAccountResponse } from "../types";

const BASE_URL = "/api/auth";
const MEMORY_BASE_URL = "/api/memories";

export const registerUser = async (userData: UserCreate): Promise<User> => {
  const response = await fetch(`${BASE_URL}/users/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(userData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    // Handle your backend's error format
    const errorMessage = errorData.message || errorData.detail || `HTTP error! status: ${response.status}`;
    throw new Error(errorMessage);
  }

  return response.json();
};

export const loginUser = async (credentials: URLSearchParams): Promise<Token> => {
    const response = await fetch(`${BASE_URL}/token`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: credentials,
    });

    if (!response.ok) {
        const errorData = await response.json();
        // Handle your backend's error format
        const errorMessage = errorData.message || errorData.detail || `HTTP error! status: ${response.status}`;
        throw new Error(errorMessage);
    }

    return response.json();
};


export const getCurrentUser = async (token: string): Promise<User> => {
  const response = await fetch(`${BASE_URL}/users/me`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    // Handle your backend's error format
    const errorMessage = errorData.message || errorData.detail || `HTTP error! status: ${response.status}`;
    throw new Error(errorMessage);
  }

  return response.json();
};

// API Key Management Functions
export const getApiKey = async (token: string): Promise<ApiKeyResponse> => {
  const response = await fetch(`${BASE_URL}/users/me/api-key`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    // Handle your backend's error format
    const errorMessage = errorData.message || errorData.detail || `HTTP error! status: ${response.status}`;
    throw new Error(errorMessage);
  }

  return response.json();
};

export const createApiKey = async (token: string): Promise<CreateApiKeyResponse> => {
  const response = await fetch(`${BASE_URL}/users/me/api-key`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    // Handle your backend's error format
    const errorMessage = errorData.message || errorData.detail || `HTTP error! status: ${response.status}`;
    throw new Error(errorMessage);
  }

  return response.json();
};

export const revokeApiKey = async (token: string): Promise<RevokeApiKeyResponse> => {
  const response = await fetch(`${BASE_URL}/users/me/api-key`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    // Handle your backend's error format
    const errorMessage = errorData.message || errorData.detail || `HTTP error! status: ${response.status}`;
    throw new Error(errorMessage);
  }

  return response.json();
};

// Memory Graph API
export const getMemoryGraph = async (token: string): Promise<MemoryGraphResponse> => {
  const response = await fetch(`${MEMORY_BASE_URL}/graph`, {
    method: "GET",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    const errorMessage = errorData.message || errorData.detail || `HTTP error! status: ${response.status}`;
    throw new Error(errorMessage);
  }

  return response.json();
};

// Memory Management API Functions
export const createMemory = async (token: string, memoryData: CreateMemoryRequest): Promise<Memory> => {
  const response = await fetch(`${MEMORY_BASE_URL}/`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(memoryData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    const errorMessage = errorData.message || errorData.detail || `HTTP error! status: ${response.status}`;
    throw new Error(errorMessage);
  }

  return response.json();
};

export const updateMemory = async (token: string, memoryId: string, memoryData: UpdateMemoryRequest): Promise<Memory> => {
  const response = await fetch(`${MEMORY_BASE_URL}/${memoryId}`, {
    method: "PUT",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(memoryData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    const errorMessage = errorData.message || errorData.detail || `HTTP error! status: ${response.status}`;
    throw new Error(errorMessage);
  }

  return response.json();
};

export const deleteMemory = async (token: string, memoryId: string): Promise<DeleteMemoryResponse> => {
  const response = await fetch(`${MEMORY_BASE_URL}/${memoryId}`, {
    method: "DELETE",
    headers: {
      "Authorization": `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    const errorMessage = errorData.message || errorData.detail || `HTTP error! status: ${response.status}`;
    throw new Error(errorMessage);
  }

  return response.json();
};

// Change Password API
export const changePassword = async (token: string, oldPassword: string, newPassword: string): Promise<{ message: string }> => {
  const response = await fetch(`${BASE_URL}/users/me/password`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      old_password: oldPassword,
      new_password: newPassword,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    const errorMessage = errorData.message || errorData.detail || `HTTP error! status: ${response.status}`;
    throw new Error(errorMessage);
  }

  return response.json();
};

// Delete All Memories API
export const deleteAllMemories = async (token: string): Promise<{ message: string }> => {
  const response = await fetch(`${MEMORY_BASE_URL}/all`, {
    method: "DELETE",
    headers: {
      "Authorization": `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    const errorMessage = errorData.message || errorData.detail || `HTTP error! status: ${response.status}`;
    throw new Error(errorMessage);
  }

  return response.json();
};

// Get Processed User Profile API
export const getProcessedUserProfile = async (token: string): Promise<ProcessedUserProfile> => {
  const response = await fetch(`${MEMORY_BASE_URL}/processed-profile`, {
    method: "GET",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    const errorMessage = errorData.message || errorData.detail || `HTTP error! status: ${response.status}`;
    throw new Error(errorMessage);
  }

  return response.json();
};

// Delete Account API
export const deleteAccount = async (token: string, confirm: string): Promise<DeleteAccountResponse> => {
  const response = await fetch(`${BASE_URL}/users/me`, {
    method: "DELETE",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      confirm: confirm,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    const errorMessage = errorData.message || errorData.detail || `HTTP error! status: ${response.status}`;
    throw new Error(errorMessage);
  }

  return response.json();
}; 