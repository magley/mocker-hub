import { NavLink } from "react-router";
import "./Navbar.css";
import { getJwtRole } from "../util/localstorage";
import { useAuthStore } from "../util/store";

export function Navbar() {
    const role = useAuthStore((state) => state.role); // "" if no JWT.

    return (
        <nav>
            <NavLink className={"navlink bold"} to="/" end><span className="white">Mocker</span><span className="blue">Hub</span></NavLink>
            {
                role === '' &&
                <>
                    <NavLink className={"navlink"} to="/login" end>Log in</NavLink>
                    <NavLink className={"navlink bordered"} to="/register" end>Sign Up</NavLink>
                </>
            }
            {
                role === 'user' &&
                <>
                </>
            }
            {
                role === 'admin' &&
                <>
                </>
            }
            {
                role === 'superadmin' &&
                <>
                </>
            }
            {
                role !== '' &&
                <>
                    <NavLink className={"navlink"} to="/logout" end>Log out</NavLink>
                </>
            }
        </nav>
    );
}