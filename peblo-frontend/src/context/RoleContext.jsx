import { createContext, useContext, useState, useEffect } from 'react';

const RoleContext = createContext();

export function RoleProvider({ children }) {
    const [role, setRole] = useState(() => {
        return localStorage.getItem('peblo_role') || 'student';
    });

    const [studentId, setStudentId] = useState(() => {
        return localStorage.getItem('peblo_student_id') || '';
    });

    const [showNameModal, setShowNameModal] = useState(false);

    useEffect(() => {
        localStorage.setItem('peblo_role', role);
    }, [role]);

    useEffect(() => {
        localStorage.setItem('peblo_student_id', studentId);
    }, [studentId]);

    // Show name modal when switching to student if no ID set
    useEffect(() => {
        if (role === 'student' && !studentId) {
            setShowNameModal(true);
        }
    }, [role, studentId]);

    const confirmStudentName = (name) => {
        setStudentId(name);
        setShowNameModal(false);
    };

    return (
        <RoleContext.Provider
            value={{
                role,
                setRole,
                studentId,
                setStudentId,
                showNameModal,
                setShowNameModal,
                confirmStudentName,
            }}
        >
            {children}
        </RoleContext.Provider>
    );
}

export function useRole() {
    const context = useContext(RoleContext);
    if (!context) throw new Error('useRole must be used within RoleProvider');
    return context;
}
