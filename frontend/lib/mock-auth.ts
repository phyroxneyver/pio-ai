import type { SessionUser } from "@/lib/session";

type MockLoginResponse = {
    token: string;
    user: SessionUser;
};

const DEMO_ACCOUNT = {
    correo: "admin@pioai.com",
    password: "123456",
    nombre: "Administrador Local",
    rol: "Administrador",
};

function wait(ms: number) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function loginMock(
    correo: string,
    password: string,
): Promise<MockLoginResponse> {
    await wait(900);

    const email = correo.trim().toLowerCase();
    const pass = password.trim();

    const validEmail = DEMO_ACCOUNT.correo.toLowerCase();
    const validPassword = DEMO_ACCOUNT.password;

    if (email !== validEmail || pass !== validPassword) {
        throw new Error("Correo o contraseña incorrectos");
    }

    return {
        token: "mock-jwt-token-pio-ai-local",
        user: {
            nombre: DEMO_ACCOUNT.nombre,
            rol: DEMO_ACCOUNT.rol,
            correo: DEMO_ACCOUNT.correo,
        },
    };
}

export function getDemoCredentials() {
    return {
        correo: DEMO_ACCOUNT.correo,
        password: DEMO_ACCOUNT.password,
    };
}