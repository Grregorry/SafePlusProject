import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  createAssessment,
  getAssessments,
  type Assessment,
} from "../../api/assessmentsApi";
import {
  getCurrentOrganisation,
  type Organisation,
} from "../../api/authApi";

function AccountPage() {
  const navigate = useNavigate();

  const [organisation, setOrganisation] =
    useState<Organisation | null>(null);

  const [assessments, setAssessments] = useState<Assessment[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [isCreatingAssessment, setIsCreatingAssessment] =
    useState(false);

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
        setErrorMessage("");

        const [account, existingAssessments] = await Promise.all([
          getCurrentOrganisation(accessToken),
          getAssessments(accessToken),
        ]);

        setOrganisation(account);
        setAssessments(existingAssessments);
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

  async function handleCreateAssessment() {
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
      setIsCreatingAssessment(true);
      setErrorMessage("");

      const newAssessment = await createAssessment(accessToken);

      setAssessments((currentAssessments) => [
        newAssessment,
        ...currentAssessments,
      ]);
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to create the assessment.",
      );
    } finally {
      setIsCreatingAssessment(false);
    }
  }

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

  if (errorMessage && !organisation) {
    return (
      <main className="min-h-screen bg-slate-100 p-8">
        <section className="mx-auto max-w-3xl rounded-xl bg-white p-8 shadow">
          <h1 className="text-2xl font-bold text-red-700">
            Session unavailable
          </h1>

          <p className="mt-3 text-slate-700">{errorMessage}</p>

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

  if (!organisation) {
    return null;
  }

  return (
    <main className="min-h-screen bg-slate-100 px-6 py-12">
      <section className="mx-auto max-w-5xl">
        <header className="rounded-xl bg-white p-8 shadow">
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
            SafePlus Account
          </p>

          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            {organisation.name}
          </h1>

          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <div>
              <p className="text-sm font-medium text-slate-500">
                Email
              </p>

              <p className="mt-1 text-slate-900">
                {organisation.email}
              </p>
            </div>

            <div>
              <p className="text-sm font-medium text-slate-500">
                Verification status
              </p>

              <p className="mt-1 text-slate-900">
                {organisation.is_verified
                  ? "Verified"
                  : "Not verified"}
              </p>
            </div>
          </div>

          <div className="mt-8 flex flex-wrap gap-4">
            <button
              type="button"
              onClick={handleCreateAssessment}
              disabled={isCreatingAssessment}
              className="rounded-lg bg-cyan-700 px-4 py-3 font-semibold text-white disabled:opacity-60"
            >
              {isCreatingAssessment
                ? "Creating assessment..."
                : "Start new assessment"}
            </button>

            <button
              type="button"
              onClick={() => navigate("/questions")}
              className="rounded-lg border border-slate-300 px-4 py-3 font-semibold text-slate-700"
            >
              View question library
            </button>

            <button
              type="button"
              onClick={handleLogout}
              className="rounded-lg border border-slate-300 px-4 py-3 font-semibold text-slate-700"
            >
              Log out
            </button>
          </div>

          {errorMessage && (
            <div className="mt-6 rounded-lg bg-red-50 p-4 text-red-700">
              {errorMessage}
            </div>
          )}
        </header>

        <section className="mt-8 rounded-xl bg-white p-8 shadow">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
                Assessments
              </p>

              <h2 className="mt-1 text-2xl font-bold text-slate-900">
                Assessment history
              </h2>
            </div>

            <span className="text-sm text-slate-500">
              {assessments.length} total
            </span>
          </div>

          {assessments.length === 0 ? (
            <div className="mt-8 rounded-lg border border-dashed border-slate-300 p-8 text-center">
              <h3 className="font-semibold text-slate-900">
                No assessments yet
              </h3>

              <p className="mt-2 text-slate-600">
                Start your first assessment to begin recording SafePlus
                results.
              </p>
            </div>
          ) : (
            <div className="mt-8 space-y-4">
              {assessments.map((assessment) => (
                <article
                  key={assessment.id}
                  className="rounded-lg border border-slate-200 p-5"
                >
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <p className="font-semibold text-slate-900">
                        Assessment #{assessment.id}
                      </p>

                      <p className="mt-1 text-sm text-slate-500">
                        Created{" "}
                        {new Date(
                          assessment.created_at,
                        ).toLocaleString()}
                      </p>
                    </div>

                    <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold capitalize text-amber-800">
                      {assessment.status.replace("_", " ")}
                    </span>
                  </div>

                  <div className="mt-5">
                    <button
                      type="button"
                      onClick={() =>
                        navigate(
                          `/assessments/${assessment.id}`,
                        )
                      }
                      className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
                    >
                      Open assessment
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

export default AccountPage;