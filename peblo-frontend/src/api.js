const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options = {}) {
    // Attach JWT if present
    const token = localStorage.getItem('peblo_token');
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch(`${BASE}${path}`, {
        headers,
        ...options,
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
        // Could dispatch a logout event here if status === 401
        throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
}

export const api = {
    // Auth
    login: async (username, password) => {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        return request('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData,
        });
    },
    register: (data) =>
        request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(data),
        }),
    getMe: () => request('/auth/me'),

    // Teacher
    ingestPDF: (formData) => {
        const token = localStorage.getItem('peblo_token');
        const headers = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;
        return fetch(`${BASE}/ingest`, { method: 'POST', body: formData, headers }).then(r => {
            if (!r.ok) throw new Error('Upload failed');
            return r.json();
        });
    },

    generateQuiz: (sourceId) =>
        request('/generate-quiz', {
            method: 'POST',
            body: JSON.stringify({ source_id: sourceId }),
        }),

    getIngestStatus: (sourceId) =>
        request(`/ingest/${sourceId}/status`),

    // Analytics
    getStudentAnalytics: () => request('/analytics/students'),

    // Student
    getTopics: () =>
        request('/topics'),

    getQuiz: ({ topic, studentId, difficulty, limit = 10, grade }) => {
        const params = new URLSearchParams({ topic, limit });
        if (studentId) params.set('student_id', studentId);
        if (difficulty) params.set('difficulty', difficulty);
        if (grade) params.set('grade', grade);
        return request(`/quiz?${params}`);
    },

    submitAnswer: (payload) =>
        request('/submit-answer', {
            method: 'POST',
            body: JSON.stringify(payload),
        }),
};
