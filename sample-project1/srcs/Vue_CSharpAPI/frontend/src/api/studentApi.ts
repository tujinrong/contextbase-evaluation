import { request } from './apiClient';
import type { Bootstrap, SearchCriteria, SearchResult, Lookups, StudentEditData, StudentSaveRequest, SaveResult } from './contracts';
export const studentApi = {
  bootstrap: (signal?:AbortSignal) => request<Bootstrap>('/api/students/bootstrap','GET',undefined,signal),
  search: (contextId: string, contextRevision: string, criteria: SearchCriteria, pageSize: number, sortKey: string, sortDirection: string) => request<SearchResult>('/api/students/search', 'POST', { contextId, contextRevision, criteria, pageSize, sortKey, sortDirection }),
  page: (contextId: string, contextRevision: string, page: number, pageSize: number, sortKey: string, sortDirection: string) => request<SearchResult>('/api/students/page', 'POST', { contextId, contextRevision, page, pageSize, sortKey, sortDirection }),
  clear: (contextId: string, contextRevision: string) => request<SearchResult>('/api/students/context/clear', 'POST', { contextId, contextRevision }),
  resume: (contextId: string, contextRevision: string) => request<SearchResult>('/api/students/resume', 'POST', { contextId, contextRevision }),
  options: (body: unknown, signal?: AbortSignal) => request<Lookups>('/api/students/options', 'POST', body, signal),
  get: (id: string | null, contextId: string, signal?:AbortSignal) => request<StudentEditData>(id ? `/api/students/${encodeURIComponent(id)}?returnContextId=${encodeURIComponent(contextId)}` : `/api/students/new?returnContextId=${encodeURIComponent(contextId)}`, 'GET', undefined, signal),
  save: (id: string | null, form: StudentSaveRequest) => request<SaveResult>(id ? `/api/students/${encodeURIComponent(id)}` : '/api/students', id ? 'PUT' : 'POST', form),
  remove: (id: string, expectedVersion: string, reason: string, returnContextId: string) => request<SaveResult>(`/api/students/${encodeURIComponent(id)}/soft-delete`, 'POST', { expectedVersion, reason, confirmed: true, returnContextId })
};
