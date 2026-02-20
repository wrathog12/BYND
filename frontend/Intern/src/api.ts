const API_BASE = 'http://localhost:8000';

export async function runPipeline(): Promise<any> {
    const res = await fetch(`${API_BASE}/api/pipeline/run`, { method: 'POST' });
    if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Pipeline failed with status ${res.status}`);
    }
    return res.json();
}

export async function fetchArticles(params?: {
    company?: string;
    bucket?: string;
    status?: string;
    limit?: number;
}): Promise<any> {
    const query = new URLSearchParams();
    if (params?.company) query.set('company', params.company);
    if (params?.bucket) query.set('bucket', params.bucket);
    if (params?.status) query.set('status', params.status);
    if (params?.limit) query.set('limit', String(params.limit));

    const res = await fetch(`${API_BASE}/api/articles?${query.toString()}`);
    if (!res.ok) throw new Error(`Fetch failed: ${res.status}`);
    return res.json();
}

export async function fetchStats(): Promise<any> {
    const res = await fetch(`${API_BASE}/api/articles/stats`);
    if (!res.ok) throw new Error(`Stats failed: ${res.status}`);
    return res.json();
}

export async function checkHealth(): Promise<boolean> {
    try {
        const res = await fetch(`${API_BASE}/api/health`);
        return res.ok;
    } catch {
        return false;
    }
}

export async function clearArticles(): Promise<any> {
    const res = await fetch(`${API_BASE}/api/articles/clear`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`Clear failed: ${res.status}`);
    return res.json();
}
