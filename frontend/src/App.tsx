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
import PublicSurveyQuestionnairePage from "./features/survey/PublicSurveyQuestionnairePage";
import PublicSurveyStartPage from "./features/survey/PublicSurveyStartPage";

function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <Navigate
            to="/login"
            replace
          />
        }
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
        element={<AccountPage />}
      />

      <Route
        path="/questions"
        element={<QuestionsPage />}
      />

      <Route
        path="/assessments/:assessmentId"
        element={<AssessmentSetupPage />}
      />

      <Route
        path="/assessments/:assessmentId/responses"
        element={<AssessmentResponsePage />}
      />

      <Route
        path="/assessments/:assessmentId/results"
        element={<AssessmentResultsPage />}
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