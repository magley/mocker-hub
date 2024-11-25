import { NavLink } from "react-router";
import "./Navbar.css";

export function Navbar() {
    return (
        <nav>
            <NavLink className={"navlink bold"} to="/" end><span className="white">Mocker</span><span className="blue">Hub</span></NavLink>
            <NavLink className={"navlink"} to="/login" end>Log in</NavLink>
            <NavLink className={"navlink bordered"} to="/register" end>Sign Up</NavLink>
        </nav>
    );
}