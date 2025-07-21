import { NavLink } from "react-router";
import "./Navbar.css";
import { useAuthStore } from "../util/store";
import { getJwtUsername } from "../util/localstorage";
import { useState, useRef } from "react";
import { useClickAway } from "react-use";

export function Navbar() {
    const role = useAuthStore((state) => state.role); // "" if no JWT.
    const username = getJwtUsername(); 
    const [showDropdown, setShowDropdown] = useState(false);
    const dropdownRef = useRef(null);
    const handleDropdownClick = () => setShowDropdown(false);

    useClickAway(dropdownRef, () => {
        setShowDropdown(false);
    });

    return (
        <nav className="navbar-container">
            {/* Left */}
            <NavLink className={"navlink bold"} to="/" end><span className="white">Mocker</span><span className="blue">Hub</span></NavLink>
            
            {/* Center*/}
            <div className="navbar-center">
            {
                role === '' &&
                <>
                    <NavLink className={"navlink"} to="/login" end>Log in</NavLink>
                    <NavLink className={"navlink bordered"} to="/register" end>Sign Up</NavLink>
                </>
            }
            {
                role === 'superadmin' &&
                <>
                    <NavLink className={"navlink"} to="/register-admin" end>New admin</NavLink>

                </>
            }
            {
                role !== '' &&
                <>
                    <NavLink className={"navlink"} to="/." end>Explore</NavLink>
                    <NavLink className={"navlink"} to={`/u/${username}/repos`} end>Repositories</NavLink>
                    <NavLink className={"navlink"} to={`/u/${username}/orgs`} end>Organisations</NavLink>
                </>
            }
                        {
                (role === 'admin' || role === 'superadmin') &&
                <>
                    <NavLink className={"navlink"} to="" end>Users</NavLink>
                    <NavLink className={"navlink"} to="" end>Analytics</NavLink>
                </>
            }
            </div>

            {/* Right: Account Dropdown */}
            {
                role !== '' &&
                <>
                <div className="navbar-right" ref={dropdownRef}>
                <span className="username"  onClick={() => setShowDropdown(!showDropdown)}>
                    {username} </span>
                    {showDropdown && (
                        <div className="dropdown-menu">
                            <NavLink to={`/u/${username}/profile`} onClick={handleDropdownClick}>Profile</NavLink>
                            {role === "user" && (
                            <NavLink to={`/u/${username}/starred`} onClick={handleDropdownClick}>Starred Repositories</NavLink>
                            )}
                            <NavLink to="/logout" onClick={handleDropdownClick}>Log out</NavLink>
                        </div>
                    )}
                </div>
                </>
            }
        </nav>
    );
}