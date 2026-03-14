import { useState } from 'react';
import { FileText } from 'lucide-react';
import Button from '../../components/Button/Button';
import StatusBadge from '../../components/StatusBadge/StatusBadge';
import { api } from '../../api';
import styles from './SourceCard.module.css';

export default function SourceCard({ source }) {
    const [generating, setGenerating] = useState(false);
    const [message, setMessage] = useState('');

    const handleGenerate = async () => {
        setGenerating(true);
        setMessage('');
        try {
            await api.generateQuiz(source.source_id);
            setMessage('Quiz generation queued ✓');
        } catch (err) {
            setMessage('Generation failed. Try again.');
        } finally {
            setGenerating(false);
        }
    };

    return (
        <div className={styles.card}>
            <div className={styles.header}>
                <FileText size={18} className={styles.fileIcon} />
                <span className={styles.filename}>{source.filename}</span>
            </div>

            <div className={styles.meta}>
                <span>Grade {source.grade || '—'}</span>
                <span className={styles.metaSep}>·</span>
                <span>{source.subject || 'General'}</span>
                <span className={styles.metaSep}>·</span>
                <StatusBadge status={source.status} />
                {source.chunk_count > 0 && (
                    <>
                        <span className={styles.metaSep}>·</span>
                        <span>{source.chunk_count} chunks</span>
                    </>
                )}
            </div>

            <div className={styles.actions}>
                {source.status === 'completed' && (
                    <Button
                        variant="secondary"
                        size="sm"
                        loading={generating}
                        onClick={handleGenerate}
                    >
                        {generating ? 'Generating…' : 'Generate Quiz'}
                    </Button>
                )}
                {message && <span className={styles.message}>{message}</span>}
            </div>
        </div>
    );
}
