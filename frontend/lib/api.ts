/**
 * API Client for SmartParlay Backend
 * Base URL: http://localhost:8000
 */

import axios from 'axios';
import type {
  Game,
  Player,
  PlayerMarginal,
  PlayerProp,
  ParlayRequest,
  ParlayRecommendation,
} from './types';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds (simulations can take time)
});

// Request interceptor for adding auth tokens (future)
api.interceptors.request.use(
  (config) => {
    // Add auth token here when implemented
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Backend returned an error response
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      // Request was made but no response received
      console.error('Network Error:', error.message);
    } else {
      // Something else happened
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

/**
 * Games API
 */
export const gamesApi = {
  /**
   * Get list of games
   * @param params - Query parameters (sport, status, upcoming)
   */
  list: async (params?: {
    sport?: string;
    status?: string;
    upcoming?: boolean;
  }): Promise<Game[]> => {
    const response = await api.get<Game[]>('/api/v1/games', { params });
    return response.data;
  },

  /**
   * Get a specific game by ID
   */
  get: async (gameId: string): Promise<Game> => {
    const response = await api.get<Game>(`/api/v1/games/${gameId}`);
    return response.data;
  },
};

/**
 * Players API
 */
export const playersApi = {
  /**
   * Get players for a specific game
   */
  listByGame: async (gameId: string): Promise<Player[]> => {
    const response = await api.get<Player[]>(`/api/v1/players/game/${gameId}`);
    return response.data;
  },

  /**
   * Get player props (betting lines) for a game
   */
  getProps: async (gameId: string): Promise<PlayerProp[]> => {
    const response = await api.get<PlayerProp[]>(
      `/api/v1/players/game/${gameId}/props`
    );
    return response.data;
  },

  /**
   * Get player marginals (projected stats) for a game
   * @deprecated Use getProps instead
   */
  getMarginals: async (gameId: string): Promise<PlayerMarginal[]> => {
    const response = await api.get<PlayerMarginal[]>(
      `/api/v1/players/game/${gameId}/marginals`
    );
    return response.data;
  },
};

/**
 * Parlay API
 */
export const parlayApi = {
  /**
   * Generate a parlay recommendation
   */
  generate: async (request: ParlayRequest): Promise<ParlayRecommendation> => {
    const response = await api.post<ParlayRecommendation>(
      '/api/v1/parlays/generate',
      request
    );
    return response.data;
  },

  /**
   * Get parlay history (future)
   */
  history: async (): Promise<ParlayRecommendation[]> => {
    const response = await api.get<ParlayRecommendation[]>('/api/v1/parlays/history');
    return response.data;
  },
};

/**
 * Health check
 */
export const healthApi = {
  check: async (): Promise<{ status: string; version: string }> => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
