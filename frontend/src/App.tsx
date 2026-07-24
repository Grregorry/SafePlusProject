import { useEffect, useState } from "react";
import { getHealthStatus } from "./api/healthApi";

function App() {
  const [backendStatus, setBackendStatus] = useState("Checking...");
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    async function checkBackend() {
      try {
        const result = await getHealthStatus();
        setBackendStatus(result.status);
        setHasError(false);
      } catch (error) {
        console.error(error);
        setBackendStatus("Unable to connect");
        setHasError(true);
      }
    }

    void checkBackend();
  }, []);

  return (
    <main className="min-h-screen bg-slate-100 p-10">
      <section className="mx-auto max-w-4xl rounded-xl bg-white p-8 shadow">
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
          SafePlus Tool
        </p>

        <h1 className="mt-2 text-4xl font-bold text-slate-900">
          Development environment ready
        </h1>

        <p className="mt-4 text-slate-600">
          React, TypeScript, Vite, Tailwind and FastAPI are configured.
        </p>

        <div className="mt-8 rounded-lg border border-slate-200 p-4">
          <p className="text-sm font-medium text-slate-500">
            Backend connection
          </p>

          <p
            className={`mt-1 text-xl font-bold ${
              hasError ? "text-red-600" : "text-green-600"
            }`}
          >
            {backendStatus}
          </p>
        </div>
      </section>
    </main>
  );
}

export default App;