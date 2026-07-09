import { api } from './client'
import type { ListeningPassage, PassageSource } from '../types/speaking'

export const listeningApi = {
  getPassage: (mode: PassageSource = 'fixed') => api.get<ListeningPassage>(`/listening/passage?mode=${mode}`),
}
