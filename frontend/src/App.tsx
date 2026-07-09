import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { DashboardPage } from './pages/DashboardPage'
import { ReadingPage } from './pages/ReadingPage'
import { SpeakingPage } from './pages/SpeakingPage'
import { WritingPage } from './pages/WritingPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="reading" element={<ReadingPage />} />
          <Route path="writing" element={<WritingPage />} />
          <Route path="speaking" element={<SpeakingPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
