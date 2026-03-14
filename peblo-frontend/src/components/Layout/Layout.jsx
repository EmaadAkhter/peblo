import { useAuth } from '../../context/AuthContext';
import styles from './Layout.module.css';

export default function Layout({ children }) {
    const { user, logout } = useAuth();

    return (
        <div className={styles.layout}>
            <header className={styles.header}>
                <div className={styles.brand}>
                    <span className={styles.logo}>
                        <span className={styles.logoAccent}>p</span>eblo
                    </span>
                    {user && (
                        <span style={{ marginLeft: '12px', fontSize: '14px', color: 'var(--text-secondary)' }}>
                            Logged in as {user.username} ({user.role})
                        </span>
                    )}
                </div>
                {user && (
                    <button
                        onClick={logout}
                        style={{
                            background: 'none',
                            border: '1px solid var(--border-color)',
                            padding: '6px 12px',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            color: 'var(--text-secondary)'
                        }}
                    >
                        Sign Out
                    </button>
                )}
            </header>

            <main className={styles.main}>
                {children}
            </main>
        </div>
    );
}
