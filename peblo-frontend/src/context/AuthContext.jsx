import { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api';

const AuthContext = createContext();

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const checkAuth = async () => {
        const token = localStorage.getItem('peblo_token');
        if (!token) {
            setUser(null);
            setLoading(false);
            return;
        }
        try {
            const userData = await api.getMe();
            setUser(userData);
        } catch (err) {
            console.error("Auth check failed:", err);
            localStorage.removeItem('peblo_token');
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        checkAuth();
    }, []);

    const login = async (username, password) => {
        const data = await api.login(username, password);
        localStorage.setItem('peblo_token', data.access_token);
        await checkAuth();
    };

    const register = async (userData) => {
        await api.register(userData);
        // Automatically log in after registration
        await login(userData.username, userData.password);
    };

    const logout = () => {
        localStorage.removeItem('peblo_token');
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{
            user,
            loading,
            role: user?.role,
            studentId: user?.role === 'student' ? user.id : null,
            login,
            register,
            logout
        }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth must be used within AuthProvider');
    return context;
}

// Keep a shiv for useRole to minimize breakage during transition
export function useRole() {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useRole/useAuth must be used within AuthProvider');
    return {
        role: context.user?.role,
        studentId: context.user?.role === 'student' ? context.user.id : null,
        // Mock setRole/setStudentId if old code tries to call them
        setRole: () => { },
        setStudentId: () => { },
        showNameModal: false,
        setShowNameModal: () => { }
    };
}
