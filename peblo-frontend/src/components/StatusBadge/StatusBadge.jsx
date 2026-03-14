import styles from './StatusBadge.module.css';

const LABELS = {
    processing: 'Processing',
    completed: 'Completed',
    failed: 'Failed',
    easy: 'Easy',
    medium: 'Medium',
    hard: 'Hard',
};

export default function StatusBadge({ status }) {
    return (
        <span className={`${styles.badge} ${styles[status] || ''}`}>
            <span className={styles.dot} />
            {LABELS[status] || status}
        </span>
    );
}
