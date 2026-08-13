import api from './api';

export interface ModelStatus {
  recommendation_model_version: string;
  forecast_model_version: string;
  last_training_date: string;
  training_dataset_size: {
    products: number;
    customers: number;
    sales: number;
    inventory?: number;
  };
  recommendation_accuracy: number;
  forecast_accuracy: {
    rmse: number;
    mae: number;
  };
  current_training_status: string;
  available_versions: {
    recommendation: string[];
    forecast: string[];
  };
}

export interface TrainingProgress {
  current_stage: string;
  percentage: number;
  status: 'idle' | 'running' | 'completed' | 'failed';
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  triggered_by: string | null;
  trigger_reason: string | null;
}

export interface TrainingHistoryEntry {
  training_id: string;
  training_start_time: string;
  training_end_time: string;
  duration_seconds: number;
  duration_human: string;
  user: string;
  role: string;
  reason: string;
  dataset_sizes: {
    products?: number;
    customers?: number;
    sales?: number;
    inventory?: number;
    forecast_results?: number;
  };
  metrics: {
    recommendation_accuracy?: number;
    forecast_rmse?: number;
    forecast_mae?: number;
  };
  status: 'success' | 'failed';
  recommendation_model_version: string;
  forecast_model_version: string;
  error_message?: string;
}

export interface TrainingHistoryResponse {
  total_runs: number;
  history: TrainingHistoryEntry[];
}

export interface TrainingSettings {
  sales_threshold: number;
  customers_threshold: number;
  time_threshold_months: number;
  min_precision: number;
  max_rmse: number;
  approval_mode: 'automatic' | 'manual';
}

export interface ModelVersionEntry {
  version: string;
  status: 'TRAINING' | 'EVALUATING' | 'PENDING_APPROVAL' | 'ACTIVE' | 'REJECTED' | 'ROLLED_BACK' | 'FAILED' | 'ARCHIVED';
  trained_on: string;
  dataset_version: string;
  metrics: {
    precision_at_k?: number;
    recall_at_k?: number;
    f1_at_k?: number;
    coverage?: number;
    rmse?: number;
    mae?: number;
    mape?: number;
    r2?: number;
  };
}

export interface ModelDetails {
  model_type: string;
  version: string;
  status: string;
  dataset_version: string;
  algorithm: string;
  hyperparameters: any;
  metrics: any;
  trigger: string;
  triggered_by: string;
  training_duration: number;
  training_date: string;
  activation_date: string | null;
  deactivation_date: string | null;
  approval_user: string | null;
  approval_role: string | null;
  approval_date: string | null;
  rejection_reason: string | null;
  rollback_from: string | null;
}

export const modelManagementApi = {
  getModelStatus: () =>
    api.get<ModelStatus>('/model/status').then((r) => r.data),
    
  getTrainingProgress: () =>
    api.get<TrainingProgress>('/model/progress').then((r) => r.data),
    
  getTrainingHistory: () =>
    api.get<TrainingHistoryResponse>('/model/history').then((r) => r.data),
    
  startManualTraining: () =>
    api.post('/model/retrain/manual').then((r) => r.data),
    
  startAutomaticTraining: () =>
    api.post('/model/retrain/automatic').then((r) => r.data),
    
  verifyTrainingPassword: (password: string) =>
    api.post('/model/verify-password', { password }).then((r) => r.data),
    
  getTrainingSettings: () =>
    api.get<TrainingSettings>('/model/training-settings').then((r) => r.data),
    
  updateTrainingSettings: (settings: TrainingSettings) =>
    api.put('/model/training-settings', settings).then((r) => r.data),

  approveModel: (modelType: string, version: string) =>
    api.post(`/model/${modelType}/${version}/approve`).then((r) => r.data),

  rejectModel: (modelType: string, version: string, reason: string) =>
    api.post(`/model/${modelType}/${version}/reject`, { reason }).then((r) => r.data),

  rollbackModel: (modelType: string, version: string) =>
    api.post(`/model/${modelType}/rollback/${version}`).then((r) => r.data),

  getModelVersions: (modelType: string) =>
    api.get<ModelVersionEntry[]>(`/model/versions/${modelType}`).then((r) => r.data),

  getModelDetails: (modelType: string, version: string) =>
    api.get<ModelDetails>(`/model/${modelType}/${version}`).then((r) => r.data),
};
