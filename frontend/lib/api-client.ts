/**
 * API Client
 *
 * Axios-based client for communicating with the FastAPI backend.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  SearchRequest,
  SearchResponse,
  ResultsResponse,
  HistoryResponse,
  HealthResponse,
} from './types';

// Create axios instance with base configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 180000, // 3 minutes timeout for long-running searches (base tier can take 30-60s)
});

// Request interceptor (for logging, auth tokens in future, etc.)
apiClient.interceptors.request.use(
  (config) => {
    // Log requests in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor (for error handling)
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Handle different error types
    let errorMessage = 'An unexpected error occurred';

    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      errorMessage = 'Request timed out. The search is taking longer than expected. Please try again.';
    } else if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
      errorMessage = 'Cannot connect to backend. Please ensure the backend is running on http://localhost:8000';
    } else if (error.response) {
      // Backend returned an error response
      errorMessage = (error.response.data as any)?.detail?.message ||
                     (error.response.data as any)?.message ||
                     error.message;
    }

    // Log errors
    console.error('[API Error]', {
      message: errorMessage,
      originalError: error.message,
      status: error.response?.status,
      data: error.response?.data,
      code: error.code,
    });

    // Transform error for better handling in components
    const apiError = {
      message: errorMessage,
      status: error.response?.status,
      data: error.response?.data,
      code: error.code,
    };

    return Promise.reject(apiError);
  }
);

/**
 * API Methods
 */

export const api = {
  /**
   * Health check
   */
  health: async (): Promise<HealthResponse> => {
    const response = await apiClient.get<HealthResponse>('/api/health');
    return response.data;
  },

  /**
   * Ping endpoint
   */
  ping: async (): Promise<{ status: string }> => {
    const response = await apiClient.get('/api/ping');
    return response.data;
  },

  /**
   * Base tier search
   */
  searchBase: async (request: SearchRequest, signal?: AbortSignal): Promise<SearchResponse> => {
    const response = await apiClient.post<SearchResponse>(
      '/api/search/base',
      request,
      { signal }
    );
    return response.data;
  },

  /**
   * Network tier search (Phase 2)
   * Note: Network tier can take 2-10 minutes depending on depth
   */
  searchNetwork: async (request: SearchRequest, signal?: AbortSignal): Promise<SearchResponse> => {
    const response = await apiClient.post<SearchResponse>(
      '/api/search/network',
      request,
      {
        timeout: 600000, // 10 minutes timeout for network tier
        signal,
      }
    );
    return response.data;
  },

  /**
   * Deep tier search (Phase 3)
   * Note: Deep tier can take 5-15 minutes
   */
  searchDeep: async (request: SearchRequest, signal?: AbortSignal): Promise<SearchResponse> => {
    const response = await apiClient.post<SearchResponse>(
      '/api/search/deep',
      request,
      {
        timeout: 900000, // 15 minutes timeout for deep tier
        signal,
      }
    );
    return response.data;
  },

  /**
   * Get search results by ID
   */
  getResults: async (searchId: string): Promise<ResultsResponse> => {
    const response = await apiClient.get<ResultsResponse>(
      `/api/results/${searchId}`
    );
    return response.data;
  },

  /**
   * Get search history
   */
  getHistory: async (limit: number = 50): Promise<HistoryResponse> => {
    const response = await apiClient.get<HistoryResponse>('/api/results/', {
      params: { limit },
    });
    return response.data;
  },

  /**
   * Bookmark a search result
   */
  saveResult: async (searchId: string, label?: string): Promise<{ saved: boolean; search_id: string }> => {
    const response = await apiClient.post(`/api/results/${searchId}/save`, { label });
    return response.data;
  },

  /**
   * Remove bookmark from a search result
   */
  unsaveResult: async (searchId: string): Promise<{ saved: boolean; search_id: string }> => {
    const response = await apiClient.delete(`/api/results/${searchId}/save`);
    return response.data;
  },

  /**
   * Get bookmarked search results
   */
  getSavedSearches: async (limit: number = 100): Promise<HistoryResponse> => {
    const response = await apiClient.get<HistoryResponse>('/api/results/', {
      params: { limit, saved: true },
    });
    return response.data;
  },
};

// Export axios instance for custom requests
export default apiClient;
