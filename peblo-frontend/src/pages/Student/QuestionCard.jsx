import { useState } from 'react';
import AnswerOption from './AnswerOption';
import Button from '../../components/Button/Button';
import styles from './QuestionCard.module.css';

export default function QuestionCard({ question, onAnswer }) {
    const [selected, setSelected] = useState(null);
    const [fillAnswer, setFillAnswer] = useState('');
    const [result, setResult] = useState(null); // { is_correct, correct_answer }
    const [submitted, setSubmitted] = useState(false);

    const handleSelect = (answer) => {
        if (submitted) return;
        setSelected(answer);
        submitAnswer(answer);
    };

    const handleFillSubmit = () => {
        if (submitted || !fillAnswer.trim()) return;
        setSelected(fillAnswer.trim());
        submitAnswer(fillAnswer.trim());
    };

    const submitAnswer = async (answer) => {
        setSubmitted(true);
        try {
            const res = await onAnswer(answer);
            setResult(res);
        } catch {
            setResult({ is_correct: false, correct_answer: question.answer });
        }
    };

    const isTF = question.type === 'TrueFalse';
    const isFill = question.type === 'FillInTheBlank';

    return (
        <div className={styles.questionCard}>
            <p className={styles.questionText}>{question.question}</p>

            {isFill ? (
                <>
                    <input
                        className={styles.fillInput}
                        type="text"
                        placeholder="Type your answer…"
                        value={fillAnswer}
                        onChange={(e) => setFillAnswer(e.target.value)}
                        disabled={submitted}
                        onKeyDown={(e) => e.key === 'Enter' && handleFillSubmit()}
                    />
                    {!submitted && (
                        <div className={styles.fillSubmit}>
                            <Button
                                variant="primary"
                                size="md"
                                onClick={handleFillSubmit}
                                disabled={!fillAnswer.trim()}
                            >
                                Submit Answer
                            </Button>
                        </div>
                    )}
                </>
            ) : isTF ? (
                <div className={styles.tfContainer}>
                    {['True', 'False'].map((opt) => (
                        <AnswerOption
                            key={opt}
                            label={opt}
                            isTF
                            selected={selected === opt}
                            correct={submitted && result?.correct_answer === opt}
                            incorrect={submitted && selected === opt && !result?.is_correct}
                            disabled={submitted}
                            onClick={() => handleSelect(opt)}
                        />
                    ))}
                </div>
            ) : (
                <div className={styles.optionsList}>
                    {(question.options || []).map((opt) => (
                        <AnswerOption
                            key={opt}
                            label={opt}
                            selected={selected === opt}
                            correct={submitted && result?.correct_answer === opt}
                            incorrect={submitted && selected === opt && !result?.is_correct}
                            disabled={submitted}
                            onClick={() => handleSelect(opt)}
                        />
                    ))}
                </div>
            )}

            {submitted && result && (
                <div className={result.is_correct ? styles.feedbackCorrect : styles.feedbackIncorrect}>
                    {result.is_correct
                        ? '✓ Correct!'
                        : `✗ The answer was ${result.correct_answer}`}
                </div>
            )}
        </div>
    );
}
