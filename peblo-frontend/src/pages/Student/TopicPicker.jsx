import { useState, useEffect } from 'react';
import { api } from '../../api';
import styles from './TopicPicker.module.css';

const COLORS = ['#EAF2EC', '#FDF3E7', '#EBF5EE', '#F3E8FF', '#FFE4E6', '#E0F2FE'];

export default function TopicPicker({ onSelect }) {
    const [topics, setTopics] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchTopics = async () => {
            try {
                // Returns [{topic: "Numbers", subject: "Math"}, ...]
                const data = await api.getTopics();
                const mapped = data.map((t, i) => ({
                    topic: t.topic,
                    subject: t.subject || 'General',
                    color: COLORS[i % COLORS.length]
                }));
                setTopics(mapped);
            } catch (err) {
                console.error("Failed to fetch topics", err);
            } finally {
                setLoading(false);
            }
        };
        fetchTopics();
    }, []);

    if (loading) return <div>Loading topics...</div>;

    return (
        <div className={styles.picker}>
            <h1 className={styles.title}>Pick a topic</h1>
            <p className={styles.subtitle}>Choose what you'd like to practice today.</p>

            <div className={styles.grid}>
                {topics.length === 0 ? (
                    <p style={{ color: 'var(--text-secondary)' }}>No topics available yet.</p>
                ) : (
                    topics.map((t) => (
                        <div
                            key={t.topic}
                            className={styles.topicCard}
                            style={{ background: t.color }}
                            onClick={() => onSelect(t)}
                        >
                            <span style={{ fontSize: '0.875rem', fontWeight: 'bold', color: 'var(--text-secondary)', marginBottom: '8px', display: 'block' }}>
                                {t.subject.toUpperCase()}
                            </span>
                            <span className={styles.topicName}>{t.topic}</span>
                        </div>
                    ))
                )}
            </div>

            <p className={styles.hint}>Difficulty adjusts automatically as you answer.</p>
        </div>
    );
}
