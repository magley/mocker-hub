import { RepositoryBadge } from "../api/repo.api";
import { UserBadge } from "../api/user.api";

type CommonBadge = UserBadge | RepositoryBadge;

    
export class BadgeUtils {
    static toHumanText(badge: CommonBadge): string {
        switch (badge) {
            case "verified": return "Verified Publisher";
            case "sponsored_oss": return "Sponsored OSS";
            case "official": return "Official";
            case "none": return "None";
            default: return `${badge}`;
        }
    }

    /**
     * 
     * Usage: <i className={`bi ${BadgeUtils.toBootstrapIcon(...)}`}></i>
     */

    static toBootstrapColor(badge: CommonBadge): string {
        switch (badge) {
            case "none": return "bg-light";
            case "verified": return "bg-secondary";
            case "official": return "bg-primary";
            case "sponsored_oss": return "bg-success";
            default: return "bg-light";
        }
    }

    static toBootstrapIcon(badge: CommonBadge): string {
        switch (badge) {
            case "none": return "";
            case "verified": return "bi-patch-check-fill";
            case "official": return "bi-award";
            case "sponsored_oss": return "bi-git";
            default: return "";
        }
    }
}
