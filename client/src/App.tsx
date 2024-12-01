import { Navbar } from './components/Navbar';
import { Home } from './pages/Home';
import { NotFound } from './pages/NotFound';
import { RepoCreate } from './pages/RepoCreate';
import { UserPasswordChangeRequired } from './pages/UserPasswordChangeRequired';
import { UserRegistration } from './pages/UserRegistration';
import { BrowserRouter, Route, Routes } from "react-router";


function App() {
    return (
        <>
            <BrowserRouter>
                <Navbar />
                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/register" element={<UserRegistration />} />
                    <Route path="/password-change-required" element={<UserPasswordChangeRequired />} />
                    <Route path="/new" element={<RepoCreate />} />
                    <Route path="*" element={<NotFound />} />
                </Routes>
            </BrowserRouter>
        </>
    );
}

export default App
