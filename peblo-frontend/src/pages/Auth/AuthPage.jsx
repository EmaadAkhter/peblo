import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import Button from '../../components/Button/Button';
import styles from './AuthPage.module.css';

export default function AuthPage() {
    const { login, register } = useAuth();
    const [isLogin, setIsLogin] = useState(true);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Form fields
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState('student');
    const [grade, setGrade] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            if (isLogin) {
                await login(username, password);
            } else {
                const payload = {
                    username,
                    password,
                    role,
                };
                if (role === 'student' && grade) {
                    payload.grade = parseInt(grade, 10);
                }
                await register(payload);
            }
        } catch (err) {
            setError(err.message || 'Authentication failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.card}>
                <div className={styles.header}>
                    <h1>Peblo AI</h1>
                    <p>{isLogin ? 'Welcome back!' : 'Create an account to start learning.'}</p>
                </div>

                <form onSubmit={handleSubmit} className={styles.form}>
                    {error && <div className={styles.error}>{error}</div>}

                    <div className={styles.field}>
                        <label>Username</label>
                        <input
                            type="text"
                            required
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="e.g. emaad"
                            disabled={loading}
                        />
                    </div>

                    <div className={styles.field}>
                        <label>Password</label>
                        <input
                            type="password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            minLength={6}
                            disabled={loading}
                        />
                    </div>

                    {!isLogin && (
                        <>
                            <div className={styles.field}>
                                <label>I am a...</label>
                                <select
                                    value={role}
                                    onChange={(e) => setRole(e.target.value)}
                                    disabled={loading}
                                >
                                    <option value="student">Student</option>
                                    <option value="teacher">Teacher</option>
                                </select>
                            </div>

                            {role === 'student' && (
                                <div className={styles.field}>
                                    <label>Grade (Optional)</label>
                                    <input
                                        type="number"
                                        min="1"
                                        max="12"
                                        value={grade}
                                        onChange={(e) => setGrade(e.target.value)}
                                        placeholder="e.g. 4"
                                        disabled={loading}
                                    />
                                </div>
                            )}
                        </>
                    )}

                    <Button
                        type="submit"
                        variant="primary"
                        fullWidth
                        loading={loading}
                    >
                        {isLogin ? 'Sign In' : 'Create Account'}
                    </Button>
                </form>

                <div className={styles.footer}>
                    <p>
                        {isLogin ? "Don't have an account? " : "Already have an account? "}
                        <button
                            type="button"
                            className={styles.linkButton}
                            onClick={() => {
                                setIsLogin(!isLogin);
                                setError(null);
                            }}
                            disabled={loading}
                        >
                            {isLogin ? 'Sign up' : 'Sign in'}
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
}
