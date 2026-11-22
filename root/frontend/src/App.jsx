import { Link, NavLink, Route, Routes } from "react-router-dom";
import Identify from "./pages/Identify.jsx";
import Result from "./pages/Result.jsx";
import Library from "./pages/Library.jsx";
import Plant from "./pages/Plant.jsx";

export default function App() {
  return (
    <>
      <header>
        <div className="wrap">
          <Link to="/" className="brand">Tripura Plant Guide</Link>
          <nav>
            <NavLink to="/" end>Identify</NavLink>
            <NavLink to="/plants">Library</NavLink>
          </nav>
        </div>
      </header>
      <main className="wrap">
        <Routes>
          <Route path="/" element={<Identify />} />
          <Route path="/result/:id" element={<Result />} />
          <Route path="/plants" element={<Library />} />
          <Route path="/plants/:id" element={<Plant />} />
          <Route path="*" element={<p>Page not found.</p>} />
        </Routes>
      </main>
    </>
  );
}
