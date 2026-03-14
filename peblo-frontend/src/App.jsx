import { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout/Layout';
import TeacherDashboard from './pages/Teacher/TeacherDashboard';
import TopicPicker from './pages/Student/TopicPicker';
import QuizSession from './pages/Student/QuizSession';
import ResultsSummary from './pages/Student/ResultsSummary';
import AuthPage from './pages/Auth/AuthPage';

function StudentView() {
    const [view, setView] = useState('picker'); // picker | quiz | results
    const [topicInfo, setTopicInfo] = useState(null);
    const [resultsData, setResultsData] = useState(null);

    const handleTopicSelect = (topic) => {
        setTopicInfo(topic);
        setView('quiz');
    };

    const handleFinish = (data) => {
        setResultsData(data);
        setView('results');
    };

    const handleRetry = () => {
        setView('quiz');
    };

    const handleNewTopic = () => {
        setTopicInfo(null);
        setResultsData(null);
        setView('picker');
    };

    if (view === 'results' && resultsData) {
        return (
            <ResultsSummary
                data={resultsData}
                onRetry={handleRetry}
                onNewTopic={handleNewTopic}
            />
        );
    }

    if (view === 'quiz' && topicInfo) {
        return (
            <QuizSession
                topicInfo={topicInfo}
                onFinish={handleFinish}
                onBack={handleNewTopic}
            />
        );
    }

    return <TopicPicker onSelect={handleTopicSelect} />;
}

function AppContent() {
    const { user, loading, role } = useAuth();

    if (loading) {
        return (
            <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ color: 'var(--text-secondary)' }}>Loading...</div>
            </div>
        );
    }

    if (!user) {
        return <AuthPage />;
    }

    return (
        <Layout>
            {role === 'teacher' ? <TeacherDashboard /> : <StudentView />}
        </Layout>
    );
}

export default function App() {
    return (
        <AuthProvider>
            <AppContent />
        </AuthProvider>
    );
}
