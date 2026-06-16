import apiClient from './client'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  message: string
  created_at: string
}

export interface ChatRequest {
  conversation_id?: string
  message: string
}

export interface ChatResponse {
  conversation_id: string
  message: string
}

export interface ConversationHistoryResponse {
  conversation_id: string
  history: ChatMessage[]
}

export const coachApi = {
  chat: async (data: ChatRequest): Promise<ChatResponse> => {
    const res = await apiClient.post<{ success: boolean; data: ChatResponse }>('/coach/chat', data)
    return res.data.data
  },
  
  history: async (conversationId: string): Promise<ConversationHistoryResponse> => {
    const res = await apiClient.get<{ success: boolean; data: ConversationHistoryResponse }>(`/coach/history`, {
      params: { conversation_id: conversationId }
    })
    return res.data.data
  }
}
