import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  getCurrentOrganisation,
  type Organisation,
} from "../../api/authApi";

function AccountPage() {
  const navigate = useNavigate();

  const [organisation, setOrganisation] =
    useState<Organisation | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    async function loadAccount() {
      const accessToken = localStorage.getItem(
        "safeplus_access_token",
      );

      if (!accessToken) {
        navigate("/login", {
          replace: true,
        });
        return;
      }

      try {
        const account = await getCurrentOrganisation(accessToken);
        setOrganisation(account);
      } catch (error) {
        localStorage.removeItem("safeplus_access_token");

        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Your session could not be verified.",
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadAccount();
  }, [navigate]);

  function handleLogout() {
    localStorage.removeItem("safeplus_access_token");
    navigate("/login");
  }

  if (isLoading) {
    return (
      <main className="min-h-screen bg-slate-100 p-8">
        <p>Loading account...</p>
      </main>
    );
  }

  if (errorMessage || !organisation) {
    return (
      <main className="min-h-screen bg-slate-100 p-8">
        <section className="mx-auto max-w-3xl rounded-xl bg-white p-8 shadow">
          <h1 className="text-2xl font-bold text-red-700">
            Session unavailable
          </h1>

          <p className="mt-3 text-slate-700">
            {errorMessage || "Please log in again."}
          </p>

          <button
            type="button"
            onClick={() => navigate("/login")}
            className="mt-6 rounded-lg bg-cyan-700 px-4 py-2 font-semibold text-white"
          >
            Return to login
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-100 px-6 py-12">
      <section className="mx-auto max-w-3xl rounded-xl bg-white p-8 shadow">
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
          SafePlus Account
        </p>

        <h1 className="mt-2 text-3xl font-bold text-slate-900">
          {organisation.name}
        </h1>

        <dl className="mt-8 space-y-4">
          <div>
            <dt className="text-sm font-medium text-slate-500">
              Email
            </dt>

            <dd className="mt-1 text-slate-900">
              {organisation.email}
            </dd>
          </div>

          <div>
            <dt className="text-sm font-medium text-slate-500">
              Verification status
            </dt>

            <dd className="mt-1 text-slate-900">
              {organisation.is_verified
                ? "Verified"
                : "Not verified"}
            </dd>
          </div>
        </dl>

        <div className="mt-8 flex flex-wrap gap-4">
          <button
            type="button"
            onClick={() => navigate("/questions")}
            className="rounded-lg bg-cyan-700 px-4 py-3 font-semibold text-white"
          >
            View assessment questions
          </button>

          <button
            type="button"
            onClick={handleLogout}
            className="rounded-lg border border-slate-300 px-4 py-3 font-semibold text-slate-700"
          >
            Log out
          </button>
        </div>
      </section>
    </main>
  );
}

export default AccountPage;