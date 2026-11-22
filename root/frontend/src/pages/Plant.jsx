import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getPlant } from "../api.js";
import Specimen from "../components/Specimen.jsx";
import { commonName, plantImage, plantInfo } from "../plantData.js";

export default function Plant() {
  const { id } = useParams();
  const [plant, setPlant] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setPlant(null);
    setError("");
    getPlant(id).then(setPlant).catch((e) => setError(e.message));
  }, [id]);

  if (error) return <p className="err">{error}</p>;
  if (!plant) return <p>Loading…</p>;

  const uses = (plantInfo(plant).uses || plant.uses || []).slice(0, 2);

  return (
    <>
      <p><Link to="/plants">Back to library</Link></p>
      <Specimen src={plantImage(plant)} alt={commonName(plant)} hint="Photo not added" />
      <h1 className="sci">{plant.scientific_name}</h1>
      <p className="lede">
        {commonName(plant)}
        {plant.local_name && <> · {plant.local_name}</>}
        {plant.family && <> · Family {plant.family}</>}
      </p>

      <h2>Medicinal uses</h2>
      {uses.length > 0
        ? <ul>{uses.map((u) => <li key={u}>{u}</li>)}</ul>
        : <p>No uses recorded for this plant yet.</p>}

      {plant.description && <p>{plant.description}</p>}
      {plant.parts_used?.length > 0 && (<><h2>Parts used</h2>
        <div>{plant.parts_used.map((p) => <span className="tag" key={p}>{p}</span>)}</div></>)}
      {plant.properties && (<><h2>Ayurvedic properties</h2><p>{plant.properties}</p></>)}
      {plant.habitat && (<><h2>Where it grows in Tripura</h2><p>{plant.habitat}</p></>)}
    </>
  );
}
