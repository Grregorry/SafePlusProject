import { Link } from "react-router-dom";

const benefits = [
  {
    title: "Built on the WorkSafe SafePlus framework",
    description:
      "Your results are benchmarked against a recognised, government-backed health and safety maturity model — not a generic checklist.",
  },
  {
    title: "Honest input from the people who matter",
    description:
      "Employees and senior managers respond separately and confidentially, surfacing the gaps between what leadership believes and what the floor actually experiences.",
  },
  {
    title: "AI-powered analysis, not just a score",
    description:
      "Every completed assessment can generate a plain-English report with curated guidance on where to focus first and why.",
  },
  {
    title: "Track maturity over time",
    description:
      "Run repeat assessments to see whether your safety culture is genuinely improving, domain by domain.",
  },
];

const steps = [
  {
    number: "1",
    title: "Register your organisation",
    description:
      "Create a free account and set up your first assessment in under a minute.",
  },
  {
    number: "2",
    title: "Share the survey link",
    description:
      "Send one link to employees and senior managers. No accounts or logins needed for respondents.",
  },
  {
    number: "3",
    title: "Get your maturity report",
    description:
      "Watch responses come in live, then generate scored results and AI-backed recommendations.",
  },
];

function LandingPage() {
  return (
    <main className="min-h-screen bg-white">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <p className="text-lg font-bold tracking-tight text-cyan-700">
            SafePlus Tool
          </p>

          <nav className="flex items-center gap-3">
            <Link
              to="/login"
              className="rounded-lg px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
            >
              Sign in
            </Link>

            <Link
              to="/register"
              className="rounded-full bg-cyan-700 px-5 py-2 text-sm font-semibold text-white hover:bg-cyan-800"
            >
              Register
            </Link>
          </nav>
        </div>
      </header>

      <section className="mx-auto grid max-w-6xl gap-12 px-6 py-16 lg:grid-cols-2 lg:items-center lg:py-24">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
            For employers and safety leaders
          </p>

          <h1 className="mt-4 text-4xl font-bold leading-tight text-slate-900 sm:text-5xl">
            Find out where your workplace safety culture really stands.
          </h1>

          <p className="mt-6 text-lg text-slate-600">
            SafePlus Tool turns the WorkSafe SafePlus framework into a survey
            your employees and managers can complete in minutes — then
            scores the results and tells you exactly where to focus next.
          </p>

          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              to="/register"
              className="rounded-full bg-cyan-700 px-6 py-3 font-semibold text-white hover:bg-cyan-800"
            >
              Register your organisation
            </Link>

            <Link
              to="/login"
              className="rounded-full border border-slate-300 px-6 py-3 font-semibold text-slate-700 hover:bg-slate-50"
            >
              Sign in
            </Link>
          </div>

          <p className="mt-4 text-sm text-slate-500">
            Free to start. No credit card required.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-8 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
            Assessment 1 · Preview
          </p>

          <h2 className="mt-2 text-xl font-bold text-slate-900">
            Overall maturity
          </h2>

          <div className="mt-6 space-y-4">
            {[
              { label: "Leadership", value: 82 },
              { label: "Worker engagement", value: 68 },
              { label: "Risk management", value: 74 },
            ].map((row) => (
              <div key={row.label}>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-slate-700">
                    {row.label}
                  </span>
                  <span className="font-semibold text-slate-900">
                    {row.value}%
                  </span>
                </div>

                <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-slate-200">
                  <div
                    className="h-full rounded-full bg-cyan-700"
                    style={{ width: `${row.value}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-8 rounded-xl bg-white p-4 text-sm text-slate-600 shadow-sm">
            "Worker engagement is your biggest opportunity — responses show
            employees want more say in how hazards are managed day to day."
          </div>
        </div>
      </section>

      <section className="border-t border-slate-100 bg-slate-50 py-16">
        <div className="mx-auto max-w-6xl px-6">
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
            Why employers choose SafePlus
          </p>

          <h2 className="mt-2 max-w-2xl text-3xl font-bold text-slate-900">
            Everything you need to measure and improve safety maturity.
          </h2>

          <div className="mt-10 grid gap-6 sm:grid-cols-2">
            {benefits.map((benefit) => (
              <div
                key={benefit.title}
                className="rounded-xl bg-white p-6 shadow-sm"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-cyan-100 text-cyan-700">
                  <svg
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    className="h-5 w-5"
                  >
                    <path
                      fillRule="evenodd"
                      d="M16.704 5.29a1 1 0 0 1 0 1.415l-7.25 7.25a1 1 0 0 1-1.415 0l-3.25-3.25a1 1 0 1 1 1.415-1.415l2.542 2.543 6.543-6.543a1 1 0 0 1 1.415 0Z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>

                <h3 className="mt-4 text-lg font-bold text-slate-900">
                  {benefit.title}
                </h3>

                <p className="mt-2 text-slate-600">
                  {benefit.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16">
        <div className="mx-auto max-w-6xl px-6">
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
            How it works
          </p>

          <h2 className="mt-2 max-w-2xl text-3xl font-bold text-slate-900">
            From registration to results in three steps.
          </h2>

          <div className="mt-10 grid gap-8 sm:grid-cols-3">
            {steps.map((step) => (
              <div key={step.number}>
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-900 font-bold text-white">
                  {step.number}
                </div>

                <h3 className="mt-4 text-lg font-bold text-slate-900">
                  {step.title}
                </h3>

                <p className="mt-2 text-slate-600">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-slate-100 bg-slate-900 py-16">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <h2 className="text-3xl font-bold text-white">
            Ready to see where your organisation stands?
          </h2>

          <p className="mt-4 text-slate-300">
            Register in minutes and start your first SafePlus assessment
            today — free, and built for employers who take safety
            seriously.
          </p>

          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <Link
              to="/register"
              className="rounded-full bg-cyan-600 px-6 py-3 font-semibold text-white hover:bg-cyan-500"
            >
              Register your organisation
            </Link>

            <Link
              to="/login"
              className="rounded-full border border-slate-600 px-6 py-3 font-semibold text-white hover:bg-slate-800"
            >
              Sign in
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-slate-100 py-8">
        <div className="mx-auto max-w-6xl px-6 text-sm text-slate-500">
          SafePlus Tool — AI-enabled health and safety maturity assessment
          platform.
        </div>
      </footer>
    </main>
  );
}

export default LandingPage;
