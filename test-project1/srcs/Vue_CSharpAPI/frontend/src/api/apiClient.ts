import type { ApiError } from './contracts';
let csrfToken = '';
const tabId = Array.from(crypto.getRandomValues(new Uint8Array(32)), n => n.toString(16).padStart(2, '0')).join('');
export const setCsrfToken = (token: string): void => { csrfToken = token; };
export class ApiFailure extends Error { constructor(public status: number, public detail: ApiError & Record<string, unknown>) { super(detail.message || '処理できませんでした。'); } }
export async function request<T>(path: string, method = 'GET', body?: unknown, signal?: AbortSignal): Promise<T> {
  let response: Response;
  try { response = await fetch(path, { method, credentials: 'same-origin', cache: 'no-store', signal, headers: { 'Content-Type': 'application/json', 'X-Tab-Id': tabId, ...(method === 'GET' ? {} : { RequestVerificationToken: csrfToken }) }, ...(body === undefined ? {} : { body: JSON.stringify(body) }) }); }
  catch (error) { if (error instanceof DOMException && error.name === 'AbortError') throw error; throw new ApiFailure(0, { outcome: 'unknown', messageId: 'E-COM-004', message: '通信結果を確認できません。保存した場合は再送せず、検索で確認してください。', fieldErrors: {}, correlationId: '', retryBySearch: true }); }
  const contentType = response.headers.get('Content-Type') || '';
  if (!contentType.includes('application/json')) throw new ApiFailure(response.status, { outcome: 'systemError', messageId: 'E-COM-004', message: '処理結果を確認できません。検索で確認してください。', fieldErrors: {}, correlationId: '', retryBySearch: true });
  const data = await response.json() as T;
  if (!response.ok) throw new ApiFailure(response.status, data as ApiError & Record<string, unknown>);
  return data;
}
