import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { sendFeedback } from "../api.js";
import Specimen from "../components/Specimen.jsx";

const pct = (c) => Math.round(c * 100);

export default function Result() {
  const { state } = useLocation();
  const [status, setStatus] = useState("idle"); // idle | choosing | sent | error

  if (!state?.result?.predictions?.length) {
    return (
      <>
        <h1>No result to show</h1>
        <p className="lede">Results are not kept after a refresh. Try a clearer photo of a single leaf in daylight.</p>
        <Link className="btn primary" to="/">Identify a plant</Link>
      </>
    );
  }

  const { result, preview } = state;
  const [top, ...others] = [...result.predictions].sort((a, b) => b.confidence - a.confidence);

  async function send(plantId, isCorrect) {
    try {
      await sendFeedback({ identification_id: result.id, plant_id: plantId, is_correct: isCorrect });
      setStatus("sent");
    } catch {
      setStatus("error");
    }
  }

  return (
    <>
      <Specimen src={preview} alt="Your plant photo" />
      <h1 className="sci">{top.scientific_name}</h1>
      <p className="lede">{top.common_name}</p>

      <div className="bar" role="img" aria-label={`${pct(top.confidence)} percent match`}>
        <span style={{ width: `${pct(top.confidence)}%` }} />
      </div>
      <p>{pct(top.confidence)}% match</p>
      {top.confidence < 0.6 && (
        <p className="note">Low confidence. Retake the photo closer to one leaf, in daylight, to improve the match.</p>
      )}

      <div className="row spaced">
        <Link className="btn primary" to={`/plants/${top.plant_id}`}>View plant details</Link>
        <Link className="btn" to="/">Identify another</Link>
      </div>

      {others.length > 0 && (
        <>
          <h2>Other possible matches</h2>
          <ul className="list">
            {others.map((p) => (
              <li key={p.plant_id} className="card">
                <Link to={`/plants/${p.plant_id}`} className="sci">{p.scientific_name}</Link>
                <div>{p.common_name} · {pct(p.confidence)}%</div>
              </li>
            ))}
          </ul>
        </>
      )}

      <h2>Is this the right plant?</h2>
      {status === "idle" && (
        <div className="row">
          <button className="btn" onClick={() => send(top.plant_id, true)}>Yes, it matches</button>
          <button className="btn" onClick={() => (others.length ? setStatus("choosing") : send(null, false))}>
            No, it’s different
          </button>
        </div>
      )}
      {status === "choosing" && (
        <div className="row">
          {others.map((p) => (
            <button key={p.plant_id} className="btn" onClick={() => send(p.plant_id, true)}>
              It’s {p.common_name}
            </button>
          ))}
          <button className="btn" onClick={() => send(null, false)}>None of these</button>
        </div>
      )}
      {status === "sent" && <p>Thanks. Your answer helps improve the model.</p>}
      {status === "error" && <p className="err">Your answer was not sent. Check your connection and try again.</p>}
    </>
  );
}
