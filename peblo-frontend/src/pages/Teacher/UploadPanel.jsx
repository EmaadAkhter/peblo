import { useState, useRef } from 'react';
import { UploadCloud } from 'lucide-react';
import Button from '../../components/Button/Button';
import { api } from '../../api';
import styles from './UploadPanel.module.css';

export default function UploadPanel({ onIngested }) {
    const [file, setFile] = useState(null);
    const [grade, setGrade] = useState('');
    const [subject, setSubject] = useState('');
    const [topic, setTopic] = useState('');
    const [loading, setLoading] = useState(false);
    const [toast, setToast] = useState(null);
    const [error, setError] = useState(null);
    const [dragover, setDragover] = useState(false);
    const inputRef = useRef(null);

    const handleDrop = (e) => {
        e.preventDefault();
        setDragover(false);
        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile && droppedFile.name.toLowerCase().endsWith('.pdf')) {
            setFile(droppedFile);
            setError(null);
        }
    };

    const handleFileChange = (e) => {
        const selected = e.target.files[0];
        if (selected) {
            setFile(selected);
            setError(null);
        }
    };

    const handleSubmit = async () => {
        if (!file) return;

        setLoading(true);
        setError(null);
        setToast(null);

        try {
            const formData = new FormData();
            formData.append('file', file);
            if (grade) formData.append('grade', grade);
            if (subject) formData.append('subject', subject || 'General');
            if (topic) formData.append('topic', topic);

            const result = await api.ingestPDF(formData);
            setToast(`✓ ${result.source_id} is being processed`);
            setFile(null);
            setGrade('');
            setSubject('');
            setTopic('');
            if (onIngested) onIngested({
                source_id: result.source_id,
                filename: file.name,
                grade: grade || 1,
                subject: subject || 'General',
                status: result.status || 'processing',
                chunk_count: 0
            });
        } catch (err) {
            setError('Upload failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.panel}>
            <h2 style={{ marginBottom: 16, fontFamily: 'var(--font-display)' }}>Upload PDF</h2>

            <div
                className={`${styles.dropzone} ${dragover ? styles.dragover : ''}`}
                onDrop={handleDrop}
                onDragOver={(e) => { e.preventDefault(); setDragover(true); }}
                onDragLeave={() => setDragover(false)}
                onClick={() => inputRef.current?.click()}
            >
                <UploadCloud size={40} className={styles.dropIcon} />
                <p className={styles.dropLabel}>Drop a PDF here, or click to browse</p>
                {file && <p className={styles.fileName}>{file.name}</p>}
                <input
                    ref={inputRef}
                    type="file"
                    accept=".pdf"
                    className={styles.hidden}
                    onChange={handleFileChange}
                />
            </div>

            <div className={styles.fields}>
                <div className={styles.field}>
                    <label>Grade</label>
                    <input
                        type="number"
                        min={1}
                        max={12}
                        placeholder="e.g. 1"
                        value={grade}
                        onChange={(e) => setGrade(e.target.value)}
                    />
                </div>
                <div className={styles.field}>
                    <label>Subject</label>
                    <input
                        type="text"
                        placeholder="e.g. Math"
                        value={subject}
                        onChange={(e) => setSubject(e.target.value)}
                    />
                </div>
                <div className={styles.field}>
                    <label>Topic (Optional)</label>
                    <input
                        type="text"
                        placeholder="e.g. Fractions"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                    />
                </div>
            </div>

            <div className={styles.actions}>
                <Button
                    variant="primary"
                    size="lg"
                    loading={loading}
                    disabled={!file}
                    icon={UploadCloud}
                    onClick={handleSubmit}
                >
                    Upload & Ingest
                </Button>
            </div>

            {toast && <div className={styles.toast}>{toast}</div>}
            {error && <div className={styles.errorToast}>{error}</div>}
        </div>
    );
}
