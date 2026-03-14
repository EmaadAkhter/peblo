import styles from './AnswerOption.module.css';

export default function AnswerOption({
    label,
    selected,
    correct,
    incorrect,
    disabled,
    onClick,
    isTF = false,
}) {
    const classes = [
        isTF ? styles.tfOption : styles.option,
        selected && !correct && !incorrect ? styles.selected : '',
        correct ? styles.correct : '',
        incorrect ? styles.incorrect : '',
        disabled ? styles.disabled : '',
    ].filter(Boolean).join(' ');

    return (
        <button className={classes} onClick={onClick} disabled={disabled}>
            <span className={styles.indicator}>
                {(selected || correct || incorrect) && <span className={styles.indicatorDot} />}
            </span>
            <span className={styles.label}>{label}</span>
        </button>
    );
}
