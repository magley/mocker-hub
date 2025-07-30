import { Navbar } from './components/Navbar';
import { Home } from './pages/Home';
import { NotFound } from './pages/NotFound';
import { RepoCreate } from './pages/RepoCreate';
import { UserPasswordChange } from './pages/UserPasswordChange';
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
import { RepoStarred } from './pages/RepoStarred';
import { OrganisationsOfUser } from './pages/OrgOfUser';
import { ProfilePage } from './pages/ProfilePage';
import { Analytics } from './pages/Analytics';
import { UsersManagement } from './pages/UsersManagement';
import { Explore } from './pages/Explore';

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
                    {authRoute("/password-change-required", ['superadmin'], UserPasswordChange)}

                    {/* Anybody. */}
                    {authRoute("/", [], Home)}
                    {authRoute("/login", [], UserLogin)}
                    {authRoute("/logout", [], UserLogout)}

                    {authRoute("/u/:username/repos", [], RepositoriesOfUser)}
                    {authRoute("/u/:username/orgs", [], OrganisationsOfUser)}
                    {authRoute("/u/:username/starred", [], RepoStarred)}
                    {authRoute("/r/*", [], RepositoryPage)}
                    {authRoute("/o/*", [], OrganizationPage)}

                    {/* Any role. */}
                    {authRoute("/password-change", ['user', 'admin', 'superadmin'], UserPasswordChange)}
                    {authRoute("/u/:username", ['user', 'admin', 'superadmin'], ProfilePage)}
                    {authRoute("/explore", ['user', 'admin', 'superadmin'], Explore)}

                    {/* Protected routes. */}
                    {authRoute("/new", ['user', 'admin'], RepoCreate)}
                    {authRoute("/org", ['user', 'admin'], OrganizationCreate)}
                    {authRoute("/analytics", ['admin', 'superadmin'], Analytics)}
                    {authRoute("/users/management", ['admin', 'superadmin'], UsersManagement)}

                    {/* "Not found", must be at the end. */}
                    {authRoute("*", [], NotFound)}
                </Routes>
                <TheToastContainer />
            </BrowserRouter>
        </>
    );
}

export default App
