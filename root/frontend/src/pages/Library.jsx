import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listPlants } from "../api.js";
import Specimen from "../components/Specimen.jsx";
import { commonName, plantImage } from "../plantData.js";

export default function Library() {
  const [q, setQ] = useState("");
  const [plants, setPlants] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const t = setTimeout(() => {
      listPlants(q).then((d) => { setPlants(d); setError(""); }).catch((e) => setError(e.message));
    }, 250);
    return () => clearTimeout(t);
  }, [q]);

  return (
    <>
      <h1>Plant library</h1>
      <p className="lede">Select a plant to see its medicinal uses.</p>
      <input type="search" value={q} onChange={(e) => setQ(e.target.value)}
        placeholder="Search by plant name" aria-label="Search plants" />

      {error && <p className="err">{error}</p>}
      {plants && plants.length === 0 && <p>No plants match “{q}”. Try another name.</p>}
      {!plants && !error && <p>Loading…</p>}

      <div className="grid spaced">
        {plants?.map((p) => (
          <Link key={p.id} to={`/plants/${p.id}`} className="tile">
            <Specimen src={plantImage(p)} alt={commonName(p)} hint="Photo not added" />
            <div className="sci">{p.scientific_name}</div>
            <div>{commonName(p)}</div>
          </Link>
        ))}
      </div>
    </>
  );
}
