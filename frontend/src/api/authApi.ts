export type Organisation = {
  id: number;
  name: string;
  email: string;
  is_verified: boolean;
  created_at: string;
};

export type RegisterRequest = {
  name: string;
  email: string;
  password: string;
};

export type LoginRequest = {
  email: string;
  password: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
};

type ApiErrorResponse = {
  detail?: string;
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function getErrorMessage(response: Response): Promise<string> {
  try {
    const error = (await response.json()) as ApiErrorResponse;

    if (typeof error.detail === "string") {
      return error.detail;
    }
  } catch {
    // The response did not contain JSON.
  }

  return `Request failed with status ${response.status}.`;
}

export async function registerOrganisation(
  registration: RegisterRequest,
): Promise<Organisation> {
  const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(registration),
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json() as Promise<Organisation>;
}

export async function loginOrganisation(
  login: LoginRequest,
): Promise<TokenResponse> {
  const formData = new URLSearchParams();

  formData.set("username", login.email);
  formData.set("password", login.password);

  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json() as Promise<TokenResponse>;
}

export async function getCurrentOrganisation(
  accessToken: string,
): Promise<Organisation> {
  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json() as Promise<Organisation>;
}