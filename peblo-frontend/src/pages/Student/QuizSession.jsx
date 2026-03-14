import { useState, useEffect } from 'react';
import { ArrowRight, BookOpen, AlertTriangle } from 'lucide-react';
import { api } from '../../api';
import { useAuth } from '../../context/AuthContext';
import QuestionCard from './QuestionCard';
import ProgressBar from '../../components/ProgressBar/ProgressBar';
import StatusBadge from '../../components/StatusBadge/StatusBadge';
import Button from '../../components/Button/Button';
import styles from './QuizSession.module.css';

export default function QuizSession({ topicInfo, onFinish, onBack }) {
    const { studentId } = useAuth();
    const [questions, setQuestions] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [answered, setAnswered] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [difficulty, setDifficulty] = useState('easy');
    const [results, setResults] = useState([]); // { is_correct, new_difficulty }

    useEffect(() => {
        const fetchQuiz = async () => {
            setLoading(true);
            setError(null);
            try {
                const data = await api.getQuiz({
                    topic: topicInfo.topic,
                    studentId,
                    limit: 10,
                });
                if (data.length === 0) {
                    setQuestions([]);
                } else {
                    setQuestions(data);
                    setDifficulty(data[0]?.difficulty || 'easy');
                }
            } catch (err) {
                setError('Could not load questions. Is the backend running?');
            } finally {
                setLoading(false);
            }
        };
        fetchQuiz();
    }, [topicInfo, studentId]);

    const handleAnswer = async (selectedAnswer) => {
        const question = questions[currentIndex];
        const res = await api.submitAnswer({
            student_id: studentId,
            question_id: question.id || question._id,
            selected_answer: selectedAnswer,
        });
        setDifficulty(res.new_difficulty);
        setResults((prev) => [...prev, res]);
        setAnswered(true);
        return res;
    };

    const handleNext = () => {
        if (currentIndex >= questions.length - 1) {
            // Finished all questions
            onFinish({
                results,
                total: questions.length,
                correct: results.filter((r) => r.is_correct).length,
                startDifficulty: questions[0]?.difficulty || 'easy',
                endDifficulty: difficulty,
                topic: topicInfo.topic,
            });
        } else {
            setCurrentIndex((i) => i + 1);
            setAnswered(false);
        }
    };

    if (loading) {
        return (
            <div className={styles.session}>
                <div className={styles.skeleton} />
            </div>
        );
    }

    if (error) {
        return (
            <div className={styles.session}>
                <div className={styles.errorState}>
                    <AlertTriangle size={18} />
                    {error}
                </div>
                <Button variant="ghost" onClick={onBack}>← Back to topics</Button>
            </div>
        );
    }

    if (questions.length === 0) {
        return (
            <div className={styles.session}>
                <div className={styles.emptyState}>
                    <BookOpen size={40} className={styles.emptyIcon} />
                    <p>No questions available yet for this topic.</p>
                    <p>Ask your teacher to generate a quiz!</p>
                </div>
                <div style={{ marginTop: 16 }}>
                    <Button variant="ghost" onClick={onBack}>← Back to topics</Button>
                </div>
            </div>
        );
    }

    const progress = ((currentIndex + (answered ? 1 : 0)) / questions.length) * 100;

    return (
        <div className={styles.session}>
            <div className={styles.sessionHeader}>
                <div className={styles.topicInfo}>
                    <span className={styles.topicName}>{topicInfo.topic}</span>
                    <span className={styles.subjectBadge}>{topicInfo.subject}</span>
                </div>
                <span className={styles.progress}>
                    {currentIndex + 1} / {questions.length}
                </span>
                <StatusBadge status={difficulty} />
            </div>

            <div className={styles.progressBar}>
                <ProgressBar value={progress} />
            </div>

            <QuestionCard
                key={currentIndex}
                question={questions[currentIndex]}
                onAnswer={handleAnswer}
            />

            {answered && (
                <div className={styles.nav}>
                    <Button variant="primary" size="md" icon={ArrowRight} onClick={handleNext}>
                        {currentIndex >= questions.length - 1 ? 'See Results' : 'Next Question'}
                    </Button>
                </div>
            )}
        </div>
    );
}
