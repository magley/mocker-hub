import { Navbar } from './components/Navbar';
import { Home } from './pages/Home';
import { NotFound } from './pages/NotFound';
import { RepoCreate } from './pages/RepoCreate';
import { UserPasswordChangeRequired } from './pages/UserPasswordChangeRequired';
import { UserRegistration } from './pages/UserRegistration';
import { UserAdminRegistration } from './pages/UserAdminRegistration';
import { UserLogin } from './pages/UserLogin';
import { BrowserRouter, Route, RouteProps, Routes } from "react-router";
import { UserLogout } from './pages/UserLogout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { OrganizationCreate } from './pages/OrgCreate';
import { RepositoriesOfUser } from './pages/RepoOfUser';
import { RepositoryPage } from './pages/RepoPage';
import { TheToastContainer } from './components/TheToastContainer';
import { OrganizationPage } from './pages/OrgPage';

// This function converts:
//
// { <Route path="/new" element={<ProtectedRoute requiredRole={['user', 'admin']}><RepoCreate /></ProtectedRoute>} /> }
// 
// Into:
// { authRoute("/new", ['user', 'admin'], RepoCreate)}
//
// Always use it, for readability, unless you have a reason not to. In that case, please document your reasons.
const authRoute = (
    path: string,
    requiredRole: string | string[],
    Component: React.ComponentType
): React.ReactElement<RouteProps> => (
    <Route
        path={path}
        element={
            <ProtectedRoute requiredRole={requiredRole}>
                <Component />
            </ProtectedRoute>
        }
    />
);

function App() {
    return (
        <>
            <BrowserRouter>
                <Navbar />
                <Routes>
                    {authRoute("/register", [""], UserRegistration)}
                    {authRoute("/register-admin", ["superadmin"], UserAdminRegistration)}

                    {/* Anybody. */}
                    {authRoute("/", [], Home)}
                    {authRoute("/login", [], UserLogin)}
                    {authRoute("/logout", [], UserLogout)}

                    {authRoute("/u/:username/repos", [], RepositoriesOfUser)}
                    {authRoute("/r/*", [], RepositoryPage)}
                    {authRoute("/o/*", [], OrganizationPage)}

                    {/* Any role. */}
                    {authRoute("/password-change-required", ['user', 'admin', 'superadmin'], UserPasswordChangeRequired)}

                    {/* Protected routes. */}
                    {authRoute("/new", ['user', 'admin'], RepoCreate)}
                    {authRoute("/org", ['user', 'admin'], OrganizationCreate)}

                    {/* "Not found", must be at the end. */}
                    {authRoute("*", [], NotFound)}
                </Routes>
                <TheToastContainer />
            </BrowserRouter>
        </>
    );
}

export default App
