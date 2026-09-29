import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import AssessmentResponsePage from "./features/assessment/AssessmentResponsePage";
import AssessmentResultsPage from "./features/assessment/AssessmentResultsPage";
import AssessmentSetupPage from "./features/assessment/AssessmentSetupPage";
import QuestionsPage from "./features/assessment/QuestionsPage";
import AccountPage from "./features/auth/AccountPage";
import LoginPage from "./features/auth/LoginPage";
import RegisterPage from "./features/auth/RegisterPage";
import VerifyEmailPage from "./features/auth/VerifyEmailPage";
import LandingPage from "./features/marketing/LandingPage";
import PublicSurveyQuestionnairePage from "./features/survey/PublicSurveyQuestionnairePage";
import PublicSurveyStartPage from "./features/survey/PublicSurveyStartPage";
import AppLayout from "./layouts/AppLayout";

function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={<LandingPage />}
      />

      <Route
        path="/register"
        element={<RegisterPage />}
      />

      <Route
        path="/login"
        element={<LoginPage />}
      />

      <Route
        path="/account"
        element={
          <AppLayout>
            <AccountPage />
          </AppLayout>
        }
      />

      <Route
        path="/verify"
        element={<VerifyEmailPage />}
      />

      <Route
        path="/questions"
        element={
          <AppLayout>
            <QuestionsPage />
          </AppLayout>
        }
      />

      <Route
        path="/assessments/:assessmentId"
        element={
          <AppLayout>
            <AssessmentSetupPage />
          </AppLayout>
        }
      />

      <Route
        path="/assessments/:assessmentId/responses"
        element={
          <AppLayout>
            <AssessmentResponsePage />
          </AppLayout>
        }
      />

      <Route
        path="/assessments/:assessmentId/results"
        element={
          <AppLayout>
            <AssessmentResultsPage />
          </AppLayout>
        }
      />

      <Route
        path="/survey/:publicCode"
        element={<PublicSurveyStartPage />}
      />

      <Route
        path="/survey/submission/:submissionToken"
        element={
          <PublicSurveyQuestionnairePage />
        }
      />

      <Route
        path="*"
        element={
          <Navigate
            to="/login"
            replace
          />
        }
      />
    </Routes>
  );
}

export default App;