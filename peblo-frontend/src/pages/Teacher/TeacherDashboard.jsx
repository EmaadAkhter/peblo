import { useState, useEffect, useCallback, useRef } from 'react';
import { FolderOpen, AlertTriangle } from 'lucide-react';
import UploadPanel from './UploadPanel';
import SourceCard from './SourceCard';
import StudentResults from './StudentResults';
import { api } from '../../api';
import styles from './TeacherDashboard.module.css';

export default function TeacherDashboard() {
    const [sources, setSources] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('sources');
    const intervalRef = useRef(null);

    const fetchSources = useCallback(async () => {
        try {
            // We don't have a list endpoint in the backend, so we'll track sources locally
            // For now, load from localStorage
            const stored = JSON.parse(localStorage.getItem('peblo_sources') || '[]');
            // Refresh statuses from backend
            const updated = await Promise.all(
                stored.map(async (s) => {
                    try {
                        const status = await api.getIngestStatus(s.source_id);
                        return { ...s, ...status };
                    } catch {
                        return s;
                    }
                })
            );
            setSources(updated);
            localStorage.setItem('peblo_sources', JSON.stringify(updated));
            setError(null);

            // Check if any are still processing
            const hasProcessing = updated.some((s) => s.status === 'processing');
            if (!hasProcessing && intervalRef.current) {
                clearInterval(intervalRef.current);
                intervalRef.current = null;
            }
        } catch (err) {
            setError('Could not load sources');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchSources();
        return () => {
            if (intervalRef.current) clearInterval(intervalRef.current);
        };
    }, [fetchSources]);

    const startPolling = useCallback(() => {
        if (intervalRef.current) return;
        intervalRef.current = setInterval(fetchSources, 4000);
    }, [fetchSources]);

    const handleIngested = useCallback(() => {
        // Refresh list and start polling
        setTimeout(async () => {
            // Get the latest source ID from backend by refreshing
            const stored = JSON.parse(localStorage.getItem('peblo_sources') || '[]');
            // We need to figure out the new source's data — ingestPDF returns source_id
            // The UploadPanel doesn't pass the full result, so we just re-fetch
            await fetchSources();
            startPolling();
        }, 500);
    }, [fetchSources, startPolling]);

    const handleAddSource = useCallback((sourceData) => {
        const stored = JSON.parse(localStorage.getItem('peblo_sources') || '[]');
        stored.push(sourceData);
        localStorage.setItem('peblo_sources', JSON.stringify(stored));
        setSources([...stored]);
        startPolling();
    }, [startPolling]);

    return (
        <div className={styles.dashboard}>
            <div className={styles.columns}>
                <UploadPanel
                    onIngested={(sourceData) => {
                        if (sourceData) {
                            handleAddSource(sourceData);
                        } else {
                            handleIngested();
                        }
                    }}
                />

                <div>
                    <div className={styles.tabs}>
                        <button
                            className={`${styles.tab} ${activeTab === 'sources' ? styles.activeTab : ''}`}
                            onClick={() => setActiveTab('sources')}
                        >
                            Uploaded Sources
                        </button>
                        <button
                            className={`${styles.tab} ${activeTab === 'results' ? styles.activeTab : ''}`}
                            onClick={() => setActiveTab('results')}
                        >
                            Student Results
                        </button>
                    </div>

                    {activeTab === 'sources' ? (
                        <>
                            {loading ? (
                                <div className={styles.sourcesList}>
                                    {[1, 2].map((i) => (
                                        <div key={i} className={styles.skeleton} />
                                    ))}
                                </div>
                            ) : error ? (
                                <div className={styles.inlineError}>
                                    <AlertTriangle size={16} />
                                    {error}
                                </div>
                            ) : sources.length === 0 ? (
                                <div className={styles.empty}>
                                    <FolderOpen size={40} className={styles.emptyIcon} />
                                    <p>No PDFs uploaded yet. Upload one to get started!</p>
                                </div>
                            ) : (
                                <div className={styles.sourcesList}>
                                    {sources.map((source) => (
                                        <SourceCard key={source.source_id} source={source} />
                                    ))}
                                </div>
                            )}
                        </>
                    ) : (
                        <StudentResults />
                    )}
                </div>
            </div>
        </div>
    );
}
