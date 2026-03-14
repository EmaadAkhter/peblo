import styles from './Button.module.css';

export default function Button({
    variant = 'primary',
    size = 'md',
    loading = false,
    disabled = false,
    icon: Icon,
    children,
    ...props
}) {
    return (
        <button
            className={`${styles.btn} ${styles[variant]} ${styles[size]}`}
            disabled={disabled || loading}
            {...props}
        >
            {loading ? (
                <span className={styles.spinner} />
            ) : Icon ? (
                <Icon size={size === 'sm' ? 14 : 16} />
            ) : null}
            {!loading && children}
        </button>
    );
}
