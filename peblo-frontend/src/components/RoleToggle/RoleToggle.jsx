import { useRole } from '../../context/RoleContext';
import styles from './RoleToggle.module.css';

export default function RoleToggle() {
    const { role, setRole } = useRole();

    return (
        <div className={styles.toggle}>
            <button
                className={`${styles.option} ${role === 'teacher' ? styles.active : ''}`}
                onClick={() => setRole('teacher')}
            >
                <span className={styles.emoji}>T</span>
                <span className={styles.label}>Teacher</span>
            </button>
            <button
                className={`${styles.option} ${role === 'student' ? styles.active : ''}`}
                onClick={() => setRole('student')}
            >
                <span className={styles.emoji}>S</span>
                <span className={styles.label}>Student</span>
            </button>
        </div>
    );
}
