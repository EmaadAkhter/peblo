import styles from './Card.module.css';

export default function Card({ children, padded = true, hoverable = false, className = '', ...props }) {
    const classes = [
        styles.card,
        padded && styles.padded,
        hoverable && styles.hoverable,
        className,
    ].filter(Boolean).join(' ');

    return (
        <div className={classes} {...props}>
            {children}
        </div>
    );
}
