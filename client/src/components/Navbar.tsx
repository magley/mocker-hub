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
                    role === 'superadmin' &&
                    <>
                        <NavLink className={"navlink"} to="/register-admin" end><i className="bi bi-person-plus"></i>New admin</NavLink>
                    </>
                }
                {
                    role !== '' &&
                    <>
                        <NavLink className={"navlink"} to="/." end><i className="bi bi-search"></i>Explore</NavLink>
                        <NavLink className={"navlink"} to={`/u/${username}/repos`} end><i className="bi bi-boxes"></i>Repositories</NavLink>
                        <NavLink className={"navlink"} to={`/u/${username}/orgs`} end><i className="bi bi-building"></i>Organizations</NavLink>
                    </>
                }
                {
                    (role === 'admin' || role === 'superadmin') &&
                    <>
                        <NavLink className={"navlink"} to="" end><i className="bi bi-people"></i>Users</NavLink>
                        <NavLink className={"navlink"} to="/analytics" end><i className="bi bi-graph-up"></i>Analytics</NavLink>
                    </>
                }
            </div>

            {/* Right */}
            <div className="navbar-right" ref={dropdownRef}>
                {
                    role === '' &&
                    <>
                        <NavLink className={"navlink"} to="/login" end>Log in</NavLink>
                        <NavLink className={"navlink bordered"} to="/register" end>Sign Up</NavLink>
                    </>
                }
                {
                    role !== '' &&
                    <>
                        <span className="username" onClick={() => setShowDropdown(!showDropdown)}>{username} <i className="bi-caret-down-fill"></i> </span>
                        {showDropdown && (
                            <div className="dropdown-menu">
                                <NavLink to={`/u/${username}`} onClick={handleDropdownClick}><i className="bi bi-person"></i>Profile</NavLink>
                                {role === "user" && (
                                    <NavLink to={`/u/${username}/starred`} onClick={handleDropdownClick}><i className="bi bi-star"></i>Starred Repositories</NavLink>
                                )}
                                <NavLink to="/logout" onClick={handleDropdownClick}><i className="bi bi-box-arrow-right"></i>Log out</NavLink>
                            </div>
                        )}
                    </>
                }
            </div>
        </nav>
    );
}