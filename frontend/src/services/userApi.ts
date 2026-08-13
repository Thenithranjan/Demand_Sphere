import api from './api';
import type { PaginatedResponse, User, UserCreate, UserUpdate } from '../types';

export const userApi = {
  getAll: (params: { skip?: number; limit?: number } = {}) =>
    api.get<PaginatedResponse<User>>('/users', { params }).then((r) => r.data),

  getById: (id: string) =>
    api.get<User>(`/users/${id}`).then((r) => r.data),

  create: (data: UserCreate) =>
    api.post<User>('/users', data).then((r) => r.data),

  update: (id: string, data: UserUpdate) =>
    api.put<User>(`/users/${id}`, data).then((r) => r.data),

  delete: (id: string) =>
    api.delete(`/users/${id}`),
};
export const userService = userApi;
