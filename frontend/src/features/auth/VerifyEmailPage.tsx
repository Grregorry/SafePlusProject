import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { verifyEmail } from "../../api/authApi";

function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");

  // A link with no token needs no request, so that state is the
  // starting state rather than something an effect sets.
  const [isVerifying, setIsVerifying] =
    useState(Boolean(token));
  const [message, setMessage] = useState(
    token
      ? ""
      : "This verification link is missing a token.",
  );
  const [isSuccess, setIsSuccess] =
    useState(false);

  const hasRequestedRef = useRef(false);

  useEffect(() => {
    if (!token) {
      return;
    }

    if (hasRequestedRef.current) {
      return;
    }

    hasRequestedRef.current = true;

    async function runVerification() {
      try {
        const result = await verifyEmail(
          token as string,
        );

        setIsSuccess(result.is_verified);
        setMessage(result.message);
      } catch (error) {
        setIsSuccess(false);
        setMessage(
          error instanceof Error
            ? error.message
            : "Unable to verify this link.",
        );
      } finally {
        setIsVerifying(false);
      }
    }

    void runVerification();
  }, [token]);

  return (
    <main className="min-h-screen bg-slate-100 px-6 py-12">
      <section className="mx-auto max-w-md rounded-xl bg-white p-8 shadow">
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
          SafePlus Tool
        </p>

        <h1 className="mt-2 text-3xl font-bold text-slate-900">
          Email verification
        </h1>

        {isVerifying ? (
          <p className="mt-4 text-slate-600">
            Verifying your link...
          </p>
        ) : (
          <div
            className={`mt-4 rounded-lg p-4 ${
              isSuccess
                ? "bg-emerald-50 text-emerald-700"
                : "bg-red-50 text-red-700"
            }`}
          >
            {message}
          </div>
        )}

        <p className="mt-6 text-sm text-slate-600">
          <Link
            to="/account"
            className="font-semibold text-cyan-700"
          >
            Return to your account
          </Link>
        </p>
      </section>
    </main>
  );
}

export default VerifyEmailPage;
