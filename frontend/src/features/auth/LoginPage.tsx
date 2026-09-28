import { type FormEvent, useState } from "react";
import {
  Link,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { loginOrganisation } from "../../api/authApi";

type LocationState = {
  message?: string;
};

function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const locationState = location.state as LocationState | null;

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [showPasswordResetNotice, setShowPasswordResetNotice] =
    useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      setIsSubmitting(true);
      setErrorMessage("");

      const token = await loginOrganisation({
        email,
        password,
      });

      localStorage.setItem(
        "safeplus_access_token",
        token.access_token,
      );

      navigate("/account");
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to log in.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-100 px-6 py-12">
      <section className="mx-auto max-w-md rounded-xl bg-white p-8 shadow">
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
          SafePlus Tool
        </p>

        <h1 className="mt-2 text-3xl font-bold text-slate-900">
          Log in
        </h1>

        <p className="mt-3 text-slate-600">
          Access your organisation’s assessments and results.
        </p>

        {locationState?.message && (
          <div className="mt-6 rounded-lg bg-emerald-50 p-4 text-emerald-700">
            {locationState.message}
          </div>
        )}

        {errorMessage && (
          <div className="mt-6 rounded-lg bg-red-50 p-4 text-red-700">
            {errorMessage}
          </div>
        )}

        <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
          <div>
            <label
              htmlFor="login-email"
              className="block text-sm font-medium text-slate-700"
            >
              Email
            </label>

            <input
              id="login-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              className="mt-2 w-full rounded-lg border border-slate-300 px-4 py-3"
            />
          </div>

          <div>
            <label
              htmlFor="login-password"
              className="block text-sm font-medium text-slate-700"
            >
              Password
            </label>

            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={8}
              required
              className="mt-2 w-full rounded-lg border border-slate-300 px-4 py-3"
            />

            <button
              type="button"
              onClick={() => setShowPasswordResetNotice(true)}
              className="mt-2 text-sm font-semibold text-cyan-700"
            >
              Forgot password?
            </button>

            {showPasswordResetNotice && (
              <p className="mt-2 rounded-lg bg-slate-50 p-3 text-sm text-slate-600">
                Password reset isn't available in this prototype
                yet. Contact your administrator for a manual
                reset.
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-cyan-700 px-4 py-3 font-semibold text-white disabled:opacity-60"
          >
            {isSubmitting ? "Logging in..." : "Log in"}
          </button>
        </form>

        <p className="mt-6 text-sm text-slate-600">
          Need an account?{" "}
          <Link to="/register" className="font-semibold text-cyan-700">
            Register
          </Link>
        </p>
      </section>
    </main>
  );
}

export default LoginPage;