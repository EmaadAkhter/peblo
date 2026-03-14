import { useEffect, useState } from 'react';
import Button from '../../components/Button/Button';
import StatusBadge from '../../components/StatusBadge/StatusBadge';
import styles from './ResultsSummary.module.css';

function getPerformanceMessage(correct, total) {
    const score = total > 0 ? correct / total : 0;
    if (score >= 0.9) return 'Excellent work!';
    if (score >= 0.7) return 'Great work!';
    if (score >= 0.5) return 'Good effort!';
    return 'Keep practising!';
}

function getStrokeColor(correct, total) {
    const pct = total > 0 ? (correct / total) * 100 : 0;
    if (pct >= 70) return 'var(--correct)';
    if (pct >= 40) return 'var(--amber)';
    return 'var(--incorrect)';
}

export default function ResultsSummary({ data, onRetry, onNewTopic }) {
    const { correct, total, startDifficulty, endDifficulty, topic } = data;
    const pct = total > 0 ? (correct / total) * 100 : 0;
    const [dashOffset, setDashOffset] = useState(283); // full circumference

    const radius = 45;
    const circumference = 2 * Math.PI * radius; // ~283

    useEffect(() => {
        // Animate on mount
        const timeout = setTimeout(() => {
            setDashOffset(circumference - (circumference * pct) / 100);
        }, 100);
        return () => clearTimeout(timeout);
    }, [pct, circumference]);

    return (
        <div className={styles.results}>
            <h1 className={styles.title}>{getPerformanceMessage(correct, total)}</h1>

            <div className={styles.ringContainer}>
                <svg className={styles.ring} width="120" height="120" viewBox="0 0 100 100">
                    <circle className={styles.ringBg} cx="50" cy="50" r={radius} />
                    <circle
                        className={styles.ringFill}
                        cx="50"
                        cy="50"
                        r={radius}
                        style={{
                            stroke: getStrokeColor(correct, total),
                            strokeDasharray: circumference,
                            strokeDashoffset: dashOffset,
                        }}
                    />
                </svg>
            </div>

            <div className={styles.scoreText}>
                {correct} / {total} correct
            </div>
            <div className={styles.scoreLabel}>{topic}</div>

            <div className={styles.difficultyChange}>
                <span>Your difficulty:</span>
                <StatusBadge status={startDifficulty} />
                <span className={styles.arrow}>→</span>
                <StatusBadge status={endDifficulty} />
            </div>

            <div className={styles.actions}>
                <Button variant="secondary" onClick={onNewTopic}>
                    Try another topic
                </Button>
                <Button variant="primary" onClick={onRetry}>
                    Retry this topic
                </Button>
            </div>
        </div>
    );
}
