import { Link } from "react-router-dom";

export const NotFound = () => {
    return (
        <>
            <div>Page not found. Perhaps it's not implemented yet, or there is a typo in the URL?</div>
            <Link to={"/"}>Return home</Link>
        </>
    )
}