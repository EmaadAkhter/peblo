import { useState, useEffect, Fragment } from 'react';
import { Users, AlertTriangle, ChevronDown, ChevronRight, CheckCircle, XCircle } from 'lucide-react';
import { api } from '../../api';
import styles from './StudentResults.module.css';

export default function StudentResults() {
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [expandedRows, setExpandedRows] = useState(new Set());

    useEffect(() => {
        const fetchResults = async () => {
            try {
                const data = await api.getStudentAnalytics();
                setResults(data);
            } catch (err) {
                setError('Failed to load student results.');
            } finally {
                setLoading(false);
            }
        };
        fetchResults();
    }, []);

    const toggleRow = (id) => {
        const newExpanded = new Set(expandedRows);
        if (newExpanded.has(id)) {
            newExpanded.delete(id);
        } else {
            newExpanded.add(id);
        }
        setExpandedRows(newExpanded);
    };

    if (loading) {
        return (
            <div className={styles.container}>
                {[1, 2, 3].map(i => <div key={i} className={styles.skeleton} />)}
            </div>
        );
    }

    if (error) {
        return (
            <div className={styles.error}>
                <AlertTriangle size={20} />
                <span>{error}</span>
            </div>
        );
    }

    if (results.length === 0) {
        return (
            <div className={styles.empty}>
                <Users size={48} className={styles.emptyIcon} />
                <p>No student results yet. Students need to take a quiz first!</p>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            <table className={styles.table}>
                <thead>
                    <tr>
                        <th>Student</th>
                        <th>Topic</th>
                        <th>Score</th>
                        <th>Accuracy</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    {results.map((result, idx) => {
                        const rowId = `${result.student_id}-${result.topic}-${idx}`;
                        const isExpanded = expandedRows.has(rowId);

                        return (
                            <Fragment key={rowId}>
                                <tr
                                    className={`${styles.row} ${isExpanded ? styles.expandedRow : ''}`}
                                    onClick={() => toggleRow(rowId)}
                                >
                                    <td>
                                        <div className={styles.studentName}>
                                            <div className={styles.avatar}>
                                                {result.student_name.charAt(0).toUpperCase()}
                                            </div>
                                            {result.student_name}
                                        </div>
                                    </td>
                                    <td>
                                        <span className={styles.topicBadge}>{result.topic}</span>
                                    </td>
                                    <td>
                                        <span className={styles.score}>
                                            {result.correct_answers} / {result.total_questions}
                                        </span>
                                    </td>
                                    <td>
                                        <div className={styles.accuracyBar}>
                                            <div
                                                className={styles.accuracyFill}
                                                style={{ width: `${result.score_percentage}%`, backgroundColor: result.score_percentage >= 70 ? 'var(--correct)' : result.score_percentage >= 40 ? 'var(--warning)' : 'var(--incorrect)' }}
                                            />
                                        </div>
                                        <span className={styles.accuracyText}>{Math.round(result.score_percentage)}%</span>
                                    </td>
                                    <td className={styles.chevron}>
                                        {isExpanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                                    </td>
                                </tr>
                                {isExpanded && (
                                    <tr className={styles.detailsRow}>
                                        <td colSpan={5}>
                                            <div className={styles.detailsContent}>
                                                <h4>Answer Breakdown</h4>
                                                <ul className={styles.answerList}>
                                                    {result.answers.map((ans, i) => (
                                                        <li key={i} className={styles.answerItem}>
                                                            <div className={styles.questionHeader}>
                                                                {ans.is_correct ? (
                                                                    <CheckCircle size={16} className={styles.correctIcon} />
                                                                ) : (
                                                                    <XCircle size={16} className={styles.incorrectIcon} />
                                                                )}
                                                                <span className={styles.questionText}>{ans.question_text}</span>
                                                            </div>
                                                            <div className={styles.answerDetails}>
                                                                <div className={styles.answerBox}>
                                                                    <span className={styles.label}>Selected:</span>
                                                                    <span className={ans.is_correct ? styles.correctText : styles.incorrectText}>
                                                                        {ans.selected_answer}
                                                                    </span>
                                                                </div>
                                                                {!ans.is_correct && (
                                                                    <div className={styles.answerBox}>
                                                                        <span className={styles.label}>Correct:</span>
                                                                        <span className={styles.correctText}>{ans.correct_answer}</span>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        </td>
                                    </tr>
                                )}
                            </Fragment>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}
