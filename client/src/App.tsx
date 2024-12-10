import { Navbar } from './components/Navbar';
import { Home } from './pages/Home';
import { NotFound } from './pages/NotFound';
import { RepoCreate } from './pages/RepoCreate';
import { UserPasswordChangeRequired } from './pages/UserPasswordChangeRequired';
import { UserRegistration } from './pages/UserRegistration';
import { UserLogin } from './pages/UserLogin';
import { BrowserRouter, Route, Routes } from "react-router";
import { UserLogout } from './pages/UserLogout';

function App() {
    return (
        <>
            <BrowserRouter>
                <Navbar />
                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/register" element={<UserRegistration />} />
                    <Route path="/login" element={<UserLogin />} />
                    <Route path="/password-change-required" element={<UserPasswordChangeRequired />} />
                    <Route path="/logout" element={<UserLogout />} />
                    <Route path="/new" element={<RepoCreate />} />
                    <Route path="*" element={<NotFound />} />
                </Routes>
            </BrowserRouter>
        </>
    );
}

export default App
