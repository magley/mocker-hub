import { Buffer } from 'buffer';

export interface JWTStruct {
    id: number,
    role: string,
    must_change_password: boolean
};

export function setJWT(jwt: string) {
    localStorage.setItem("jwt", jwt);
}

export function clearJWT() {
    localStorage.removeItem("jwt");
}

export function getJWTStringOrNull(): string | null {
    return localStorage.getItem("jwt");
}

export function getJWT(jwt: string): JWTStruct {
    let parts = jwt.split(".");
    for (let i = 0; i < parts.length; i++) {
        parts[i] = Buffer.from(parts[i], 'base64').toString();
    }
    let token: JWTStruct = JSON.parse(parts[1]);
    return token;
}

export function getJwtRole(): string {
    const jwtString = getJWTStringOrNull();
    if (jwtString == null) {
        return "";
    }
    return getJWT(jwtString).role;
}

// export function getJwtUsername(): string {
//     const jwtString = getJWTStringOrNull();
//     if (jwtString == null) {
//         return "";
//     }
//     return getJWT(jwtString).sub;
// }

export function getJwtMustChangePassword(): boolean {
    const jwtString = getJWTStringOrNull();
    if (jwtString == null) {
        return false;
    }
    return getJWT(jwtString).must_change_password;
}

export function getJwtId(): number {
    const jwtString = getJWTStringOrNull();
    if (jwtString == null) {
        return -1;
    }
    return getJWT(jwtString).id;
}