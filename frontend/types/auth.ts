export type AuthUser = {
  id?: number | string;
  nombre: string;
  rol: string;
  correo?: string;
};

export type LoginResponse = {
  token: string;
  user: AuthUser;
};