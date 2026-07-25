import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { registerOrganisation } from "../../api/authApi";

function RegisterPage() {
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      setIsSubmitting(true);
      setErrorMessage("");

      await registerOrganisation({
        name,
        email,
        password,
      });

      navigate("/login", {
        state: {
          message: "Account created successfully. You can now log in.",
        },
      });
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to create the account.",
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
          Create an organisation account
        </h1>

        <p className="mt-3 text-slate-600">
          Register your organisation to begin a SafePlus assessment.
        </p>

        {errorMessage && (
          <div className="mt-6 rounded-lg bg-red-50 p-4 text-red-700">
            {errorMessage}
          </div>
        )}

        <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
          <div>
            <label
              htmlFor="organisation-name"
              className="block text-sm font-medium text-slate-700"
            >
              Organisation name
            </label>

            <input
              id="organisation-name"
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              minLength={2}
              maxLength={200}
              required
              className="mt-2 w-full rounded-lg border border-slate-300 px-4 py-3"
            />
          </div>

          <div>
            <label
              htmlFor="registration-email"
              className="block text-sm font-medium text-slate-700"
            >
              Email
            </label>

            <input
              id="registration-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              className="mt-2 w-full rounded-lg border border-slate-300 px-4 py-3"
            />
          </div>

          <div>
            <label
              htmlFor="registration-password"
              className="block text-sm font-medium text-slate-700"
            >
              Password
            </label>

            <input
              id="registration-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={8}
              maxLength={128}
              required
              className="mt-2 w-full rounded-lg border border-slate-300 px-4 py-3"
            />

            <p className="mt-2 text-sm text-slate-500">
              Use at least eight characters.
            </p>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-cyan-700 px-4 py-3 font-semibold text-white disabled:opacity-60"
          >
            {isSubmitting ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="mt-6 text-sm text-slate-600">
          Already registered?{" "}
          <Link to="/login" className="font-semibold text-cyan-700">
            Log in
          </Link>
        </p>
      </section>
    </main>
  );
}

export default RegisterPage;