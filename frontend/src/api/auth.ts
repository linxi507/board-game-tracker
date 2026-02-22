import { apiFetch } from "./client";

export type RegisterPayload = {
  username: string;
  email: string;
  password: string;
};

export type LoginPayload = {
  identifier: string;
  password: string;
};

export type AuthToken = {
  access_token: string;
  token_type: string;
};

export async function register(payload: RegisterPayload) {
  return apiFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function login(payload: LoginPayload): Promise<AuthToken> {
  return (await apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  })) as AuthToken;
}
