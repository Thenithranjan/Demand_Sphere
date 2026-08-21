/**
 * Authentication API Service — Demand Sphere Frontend
 * ===================================================
 * Exposes login endpoints and token management.
 */

import api from './api';
import type { UserLogin, TokenResponse } from '../types';

export const authApi = {
  login: (credentials: UserLogin) =>
    api.post<TokenResponse>('/users/login', credentials).then((r) => r.data),
};
