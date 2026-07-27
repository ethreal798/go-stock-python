import request from "./index";
import type {
  AIModelConfigDetailResponse,
  AIModelConfigCreateRequest,
  AIModelConfigEnabledUpdateRequest,
  AIModelConfigListResponse,
  AIModelConfigResponse,
  AIModelConfigTestRequest,
  AIModelConfigTestResponse,
  AIModelConfigUpdateRequest,
} from "@/types/settings";

export const createAIModelConfig = (data: AIModelConfigCreateRequest) =>
  request.post<AIModelConfigResponse>("/settings/ai-models", data);

export const getAIModelConfigs = () =>
  request.get<AIModelConfigListResponse>("/settings/ai-models");

export const updateAIModelConfig = (
  id: number,
  data: AIModelConfigUpdateRequest,
) => request.patch<AIModelConfigResponse>(`/settings/ai-models/${id}`, data);

export const updateAIModelConfigEnabled = (
  id: number,
  enabled: AIModelConfigEnabledUpdateRequest["enabled"],
) =>
  request.patch<AIModelConfigResponse>(`/settings/ai-models/${id}`, {
    enabled,
  } satisfies AIModelConfigEnabledUpdateRequest);

export const getAIModelConfigDetail = (id: number) =>
  request.get<AIModelConfigDetailResponse>(`/settings/ai-models/${id}`);

export const deleteAIModelConfig = (id: number) =>
  request.delete<void>(`/settings/ai-models/${id}`);

export const testAIModelConfig = (id: number) =>
  request.post<AIModelConfigTestResponse>(`/settings/ai-models/${id}/test`);

export const testAIModelConfigDraft = (data: AIModelConfigTestRequest) =>
  request.post<AIModelConfigTestResponse>("/settings/ai-models/test", data);
