import React from "react";
import LearnerDashboard from "./Dashboard";

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-slate-950 p-6 md:p-12">
      <LearnerDashboard userId="demo_student" />
    </main>
  );
}
