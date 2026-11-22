import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { identifyPlant } from "../api.js";
import Specimen from "../components/Specimen.jsx";

const getCoords = () =>
  new Promise((resolve) =>
    navigator.geolocation.getCurrentPosition((p) => resolve(p.coords), () => resolve(null), { timeout: 8000 })
  );

export default function Identify() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [withLocation, setWithLocation] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const camera = useRef();
  const gallery = useRef();
  const navigate = useNavigate();

  function pick(e) {
    const f = e.target.files?.[0];
    e.target.value = "";
    if (!f) return;
    if (!f.type.startsWith("image/")) return setError("Choose a photo in JPG or PNG format.");
    if (preview) URL.revokeObjectURL(preview);
    setError("");
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }

  async function submit() {
    setBusy(true);
    setError("");
    try {
      const coords = withLocation && navigator.geolocation ? await getCoords() : null;
      const result = await identifyPlant(file, coords);
      navigate(`/result/${result.id}`, { state: { result, preview } });
    } catch (e) {
      setError(e.message);
      setBusy(false);
    }
  }

  return (
    <>
      <h1>Identify a medicinal plant</h1>
      <p className="lede">
        Photograph a leaf, flower or bark. We match it against the plants documented in Tripura.
      </p>

      <Specimen src={preview} alt="Your plant photo" hint="Fill the frame with one leaf or flower, in daylight." />

      <input ref={camera} type="file" accept="image/*" capture="environment" className="hidden" onChange={pick} />
      <input ref={gallery} type="file" accept="image/*" className="hidden" onChange={pick} />

      <div className="row spaced">
        <button className="btn" onClick={() => camera.current.click()} disabled={busy}>Take photo</button>
        <button className="btn" onClick={() => gallery.current.click()} disabled={busy}>Choose from gallery</button>
      </div>

      <label className="check">
        <input type="checkbox" checked={withLocation} onChange={(e) => setWithLocation(e.target.checked)} />
        Add my location to this record, to help map where plants grow
      </label>

      <div className="row spaced">
        <button className="btn primary" onClick={submit} disabled={!file || busy}>
          {busy ? "Identifying…" : "Identify plant"}
        </button>
      </div>
      <p role="status" className="err">{error}</p>
    </>
  );
}
