import {
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  useLocation,
  useNavigate,
} from "react-router-dom";

import {
  getAssessments,
  type Assessment,
} from "../api/assessmentsApi";
import {
  getCurrentOrganisation,
  type Organisation,
} from "../api/authApi";
import { useConfirm } from "../components/useConfirm";

const SIDEBAR_STATE_KEY =
  "safeplus_sidebar_collapsed";

const ACCESS_TOKEN_KEY =
  "safeplus_access_token";

type AppLayoutProps = {
  children: ReactNode;
};

const iconProps = {
  className: "h-5 w-5 shrink-0",
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
};

function MenuIcon() {
  return (
    <svg {...iconProps}>
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  );
}

function DashboardIcon() {
  return (
    <svg {...iconProps}>
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
    </svg>
  );
}

function AssessmentsIcon() {
  return (
    <svg {...iconProps}>
      <rect x="4" y="4" width="16" height="16" rx="2" />
      <line x1="8" y1="9" x2="16" y2="9" />
      <line x1="8" y1="13" x2="16" y2="13" />
      <line x1="8" y1="17" x2="12" y2="17" />
    </svg>
  );
}

function LogoutIcon() {
  return (
    <svg {...iconProps}>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg {...iconProps}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  );
}

function ChevronIcon({
  className,
}: {
  className?: string;
}) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={true}
      className={className}
    >
      <polyline points="9 6 15 12 9 18" />
    </svg>
  );
}

function readCollapsedPreference(): boolean {
  try {
    return (
      localStorage.getItem(
        SIDEBAR_STATE_KEY,
      ) === "true"
    );
  } catch {
    return false;
  }
}

function AppLayout({
  children,
}: AppLayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { confirm, dialog } = useConfirm();

  const [collapsed, setCollapsed] =
    useState(readCollapsedPreference);

  const [
    organisation,
    setOrganisation,
  ] = useState<Organisation | null>(null);

  const organisationName =
    organisation?.name ?? "SafePlus";

  const [assessments, setAssessments] =
    useState<Assessment[]>([]);

  const [
    assessmentsExpanded,
    setAssessmentsExpanded,
  ] = useState(false);

  useEffect(() => {
    let accessToken: string | null;

    try {
      accessToken = localStorage.getItem(
        ACCESS_TOKEN_KEY,
      );
    } catch {
      accessToken = null;
    }

    if (!accessToken) {
      return;
    }

    let cancelled = false;

    getCurrentOrganisation(accessToken)
      .then((currentOrganisation) => {
        if (!cancelled) {
          setOrganisation(
            currentOrganisation,
          );
        }
      })
      .catch(() => {
        // Keep the fallback name; each page handles its own auth errors.
      });

    getAssessments(accessToken)
      .then((list) => {
        if (!cancelled) {
          setAssessments(list);
        }
      })
      .catch(() => {
        // Leave the list empty; each page handles its own auth errors.
      });

    return () => {
      cancelled = true;
    };
  }, [location.pathname]);

  function toggleCollapsed() {
    setCollapsed((current) => {
      const next = !current;

      try {
        localStorage.setItem(
          SIDEBAR_STATE_KEY,
          String(next),
        );
      } catch {
        // Ignore storage failures.
      }

      return next;
    });
  }

  function goToDashboard() {
    navigate("/account");

    if (location.pathname === "/account") {
      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    }
  }

  async function handleLogout() {
    const confirmed = await confirm(
      "Log out of SafePlus?\n\nYou'll need to sign in again to manage assessments.",
    );

    if (!confirmed) {
      return;
    }

    try {
      localStorage.removeItem(
        ACCESS_TOKEN_KEY,
      );
    } catch {
      // Ignore storage failures.
    }

    navigate("/login");
  }

  const isDashboardActive =
    location.pathname === "/account";

  const isAssessmentsActive =
    location.pathname.startsWith(
      "/assessments",
    );

  const showAssessmentList =
    !collapsed &&
    (assessmentsExpanded ||
      location.pathname.startsWith(
        "/assessments",
      ));

  const itemBaseClass =
    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold transition-colors";

  function itemClass(
    isActive: boolean,
  ): string {
    return [
      itemBaseClass,
      collapsed ? "justify-center" : "",
      isActive
        ? "bg-blue-600 text-white"
        : "text-slate-600 hover:bg-slate-100",
    ].join(" ");
  }

  return (
    <div className="min-h-screen bg-slate-100">
      {dialog}

      <aside
        className={`fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-slate-200 bg-white px-3 py-4 transition-[width] duration-200 ${
          collapsed ? "w-16" : "w-60"
        }`}
      >
        <div
          className={`flex items-center ${
            collapsed
              ? "justify-center"
              : "gap-3"
          }`}
        >
          <button
            type="button"
            onClick={toggleCollapsed}
            aria-label={
              collapsed
                ? "Expand sidebar"
                : "Collapse sidebar"
            }
            aria-expanded={!collapsed}
            className="rounded-lg p-2 text-slate-700 hover:bg-slate-100"
          >
            <MenuIcon />
          </button>

          {!collapsed && (
            <span className="truncate text-lg font-bold text-slate-900">
              {organisationName}
            </span>
          )}
        </div>

        <nav
          aria-label="Primary"
          className="mt-6 flex flex-col gap-1"
        >
          <button
            type="button"
            onClick={goToDashboard}
            title="Dashboard"
            aria-current={
              isDashboardActive
                ? "page"
                : undefined
            }
            className={itemClass(
              isDashboardActive,
            )}
          >
            <DashboardIcon />
            {!collapsed && (
              <span>Dashboard</span>
            )}
          </button>

          <div>
            <button
              type="button"
              onClick={() => {
                if (collapsed) {
                  toggleCollapsed();
                  setAssessmentsExpanded(true);
                  return;
                }

                setAssessmentsExpanded(
                  (value) => !value,
                );
              }}
              title="Assessments"
              aria-current={
                isAssessmentsActive
                  ? "page"
                  : undefined
              }
              aria-expanded={
                collapsed
                  ? undefined
                  : showAssessmentList
              }
              className={itemClass(
                isAssessmentsActive,
              )}
            >
              <AssessmentsIcon />
              {!collapsed && (
                <>
                  <span className="flex-1 text-left">
                    Assessments
                  </span>

                  <ChevronIcon
                    className={`h-4 w-4 shrink-0 transition-transform duration-200 ${
                      showAssessmentList
                        ? "rotate-90"
                        : ""
                    }`}
                  />
                </>
              )}
            </button>

            {!collapsed && (
              <div
                className={`grid transition-all duration-200 ease-out ${
                  showAssessmentList
                    ? "grid-rows-[1fr] opacity-100"
                    : "grid-rows-[0fr] opacity-0"
                }`}
              >
                <div className="overflow-hidden">
                  <div className="ml-4 mt-1 flex flex-col gap-0.5 border-l border-slate-200 pl-3">
                    {assessments.length ===
                    0 ? (
                      <p className="px-3 py-1.5 text-xs text-slate-400">
                        No assessments yet
                      </p>
                    ) : (
                      assessments.map(
                        (assessment) => {
                          const assessmentPath = `/assessments/${assessment.id}`;

                          const isActive =
                            location.pathname ===
                              assessmentPath ||
                            location.pathname.startsWith(
                              `${assessmentPath}/`,
                            );

                          return (
                            <button
                              key={
                                assessment.id
                              }
                              type="button"
                              onClick={() =>
                                navigate(
                                  // Closed assessments have nothing left to set up.
                                  assessment.status ===
                                    "completed"
                                    ? `/assessments/${assessment.id}/results`
                                    : `/assessments/${assessment.id}`,
                                )
                              }
                              title={
                                assessment.name
                              }
                              className={`w-full truncate rounded-md px-3 py-1.5 text-left text-xs font-medium transition-colors ${
                                isActive
                                  ? "bg-blue-50 text-blue-700"
                                  : "text-slate-600 hover:bg-slate-100"
                              }`}
                            >
                              {assessment.name}
                            </button>
                          );
                        },
                      )
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </nav>

        <div className="mt-auto">
          {!collapsed && organisation && (
            <div className="px-3 pb-3 text-sm">
              <p
                className="truncate text-slate-600"
                title={organisation.email}
              >
                {organisation.email}
              </p>

              <p className="mt-0.5 font-semibold text-slate-700">
                {organisation.is_verified
                  ? "Verified organisation"
                  : "Organisation not verified"}
              </p>
            </div>
          )}

          <div className="flex flex-col gap-1 border-t border-slate-200 pt-3">
          <button
            type="button"
            onClick={() =>
              void handleLogout()
            }
            title="Logout"
            className={`${itemBaseClass} ${
              collapsed
                ? "justify-center"
                : ""
            } text-slate-600 hover:bg-red-50 hover:text-red-700`}
          >
            <LogoutIcon />
            {!collapsed && (
              <span>Logout</span>
            )}
          </button>

          <button
            type="button"
            disabled
            aria-disabled="true"
            title="Settings — coming soon"
            className={`${itemBaseClass} ${
              collapsed
                ? "justify-center"
                : ""
            } cursor-not-allowed text-slate-300`}
          >
            <SettingsIcon />
            {!collapsed && (
              <span>Settings</span>
            )}
          </button>
          </div>
        </div>
      </aside>

      <div
        className={`transition-[padding] duration-200 ${
          collapsed ? "pl-16" : "pl-60"
        }`}
      >
        <div className="mx-auto max-w-6xl px-6 py-10">
          {children}
        </div>
      </div>
    </div>
  );
}

export default AppLayout;
