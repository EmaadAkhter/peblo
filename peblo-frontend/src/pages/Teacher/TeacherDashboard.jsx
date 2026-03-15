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
            const updated = await api.getSources();
            setSources(updated);
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
            await fetchSources();
            startPolling();
        }, 500);
    }, [fetchSources, startPolling]);

    const handleAddSource = useCallback((sourceData) => {
        // Optimistic UI update before next fetch overrides it
        setSources(prev => [sourceData, ...prev]);
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
                                        <SourceCard
                                            key={source.source_id}
                                            source={source}
                                            onDelete={(id) => setSources(prev => prev.filter(s => s.source_id !== id))}
                                        />
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
