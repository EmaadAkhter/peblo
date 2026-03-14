import styles from './ProgressBar.module.css';

export default function ProgressBar({ value = 0, color }) {
    return (
        <div className={styles.track}>
            <div
                className={styles.fill}
                style={{
                    width: `${Math.min(100, Math.max(0, value))}%`,
                    background: color || 'var(--accent)',
                }}
            />
        </div>
    );
}
