import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import AssessmentSetupPage from "./features/assessment/AssessmentSetupPage";
import QuestionsPage from "./features/assessment/QuestionsPage";
import AccountPage from "./features/auth/AccountPage";
import LoginPage from "./features/auth/LoginPage";
import RegisterPage from "./features/auth/RegisterPage";

function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={<Navigate to="/login" replace />}
      />

      <Route path="/register" element={<RegisterPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/account" element={<AccountPage />} />
      <Route path="/questions" element={<QuestionsPage />} />

      <Route
        path="/assessments/:assessmentId"
        element={<AssessmentSetupPage />}
      />

      <Route
        path="*"
        element={<Navigate to="/login" replace />}
      />
    </Routes>
  );
}

export default App;