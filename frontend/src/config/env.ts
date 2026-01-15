const DEFAULT_API_URL = "http://localhost:8001/api/v1";

const rawApiUrl = process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_API_URL;

const validateUrl = (value: string, name: string) => {
    try {
        new URL(value);
    } catch {
        throw new Error(`${name} must be a valid URL. Got: ${value}`);
    }
};

if (process.env.NODE_ENV === "production" && !process.env.NEXT_PUBLIC_API_URL) {
    throw new Error("NEXT_PUBLIC_API_URL is required in production builds");
}

validateUrl(rawApiUrl, "NEXT_PUBLIC_API_URL");

export const frontendEnv = {
    apiBaseUrl: rawApiUrl,
};
