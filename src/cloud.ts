export interface CloudFile {
  fileId: string;
  name: string;
  type: 'image' | 'pdf';
  contentType: string;
  size: number;
  processedSize?: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  createdAt: string;
  updatedAt: string;
  error?: string;
  extractedText?: string;
}

const apiUrl = import.meta.env.VITE_API_URL?.replace(/\/$/, '') as string | undefined;
const cognitoDomain = import.meta.env.VITE_COGNITO_DOMAIN?.replace(/\/$/, '') as string | undefined;
const clientId = import.meta.env.VITE_COGNITO_CLIENT_ID as string | undefined;
const redirectUri = window.location.origin + window.location.pathname;

export const configured = Boolean(apiUrl && cognitoDomain && clientId);

function base64url(bytes: Uint8Array) {
  return btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

export async function signIn() {
  if (!configured) return;
  const verifier = base64url(crypto.getRandomValues(new Uint8Array(32)));
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier));
  const state = base64url(crypto.getRandomValues(new Uint8Array(16)));
  sessionStorage.setItem('cloudlens_pkce', verifier);
  sessionStorage.setItem('cloudlens_state', state);
  const url = new URL(`${cognitoDomain}/oauth2/authorize`);
  url.search = new URLSearchParams({response_type: 'code', client_id: clientId!, redirect_uri: redirectUri,
    scope: 'openid email profile', code_challenge_method: 'S256', code_challenge: base64url(new Uint8Array(digest)), state}).toString();
  window.location.assign(url.toString());
}

export async function finishSignIn() {
  const url = new URL(window.location.href);
  const code = url.searchParams.get('code');
  if (!code) {await renewToken(); return;}
  const state = sessionStorage.getItem('cloudlens_state');
  const verifier = sessionStorage.getItem('cloudlens_pkce');
  if (!state || !verifier || state !== url.searchParams.get('state')) throw new Error('Sign-in verification failed. Please try again.');
  const result = await fetch(`${cognitoDomain}/oauth2/token`, {
    method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: new URLSearchParams({grant_type: 'authorization_code', client_id: clientId!, code,
      redirect_uri: redirectUri, code_verifier: verifier}),
  });
  if (!result.ok) throw new Error('Sign-in could not be completed.');
  const tokens = await result.json();
  sessionStorage.setItem('cloudlens_token', tokens.id_token);
  sessionStorage.setItem('cloudlens_refresh', tokens.refresh_token);
  sessionStorage.removeItem('cloudlens_pkce');
  sessionStorage.removeItem('cloudlens_state');
  window.history.replaceState({}, '', redirectUri);
}

export function signOut() {
  sessionStorage.removeItem('cloudlens_token');
  sessionStorage.removeItem('cloudlens_refresh');
  window.location.reload();
}

export function getToken() { return sessionStorage.getItem('cloudlens_token'); }

async function renewToken() {
  if (currentUser()) return;
  const refresh = sessionStorage.getItem('cloudlens_refresh');
  if (!refresh || !configured) return;
  const result = await fetch(`${cognitoDomain}/oauth2/token`, {
    method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: new URLSearchParams({grant_type: 'refresh_token', client_id: clientId!, refresh_token: refresh}),
  });
  if (!result.ok) {sessionStorage.removeItem('cloudlens_token'); sessionStorage.removeItem('cloudlens_refresh'); return;}
  const tokens = await result.json();
  sessionStorage.setItem('cloudlens_token', tokens.id_token);
  if (tokens.refresh_token) sessionStorage.setItem('cloudlens_refresh', tokens.refresh_token);
}

export function currentUser() {
  const token = getToken();
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
    if (payload.exp * 1000 < Date.now()) return null;
    return {email: payload.email as string, isAdmin: (payload['cognito:groups'] || []).includes('admins') as boolean};
  } catch { return null; }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  if (!apiUrl) throw new Error('CloudLens API URL is not configured.');
  await renewToken();
  const token = getToken();
  if (!token) throw new Error('Please sign in first.');
  const result = await fetch(`${apiUrl}${path}`, {...options, headers: {
    Authorization: `Bearer ${token}`, ...(options.body ? {'Content-Type': 'application/json'} : {}), ...options.headers,
  }});
  const body = await result.json().catch(() => ({}));
  if (!result.ok) throw new Error(body.error || (result.status === 401 ? 'Session expired. Please sign in again.' : 'Request failed.'));
  return body as T;
}

export const cloud = {
  files: () => request<{files: CloudFile[]}>('/files'),
  file: (id: string) => request<{file: CloudFile}>(`/files/${encodeURIComponent(id)}`),
  uploadUrl: (file: File) => request<{file: CloudFile; uploadUrl: string; headers: Record<string, string>}>('/upload-url', {
    method: 'POST', body: JSON.stringify({name: file.name, size: file.size, contentType: file.type}),
  }),
  remove: (id: string) => request<{deleted: boolean}>(`/files/${encodeURIComponent(id)}`, {method: 'DELETE'}),
  download: async (id: string) => {
    const {downloadUrl} = await request<{downloadUrl: string}>(`/files/${encodeURIComponent(id)}/download`);
    window.location.assign(downloadUrl);
  },
  metrics: () => request<{counts: Record<string, number>; totalOriginalBytes: number; bytesSaved: number; failureRate: number; averageLatencyMs: number}>('/admin/metrics'),
};
