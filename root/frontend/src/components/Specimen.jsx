import { useEffect, useState } from "react";

// Photo frame with viewfinder corners. Shows the hint text if the image is missing.
export default function Specimen({ src, alt = "", hint = "No photo yet", className = "" }) {
  const [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [src]);
  return (
    <div className={`frame ${className}`}>
      {src && !failed ? <img src={src} alt={alt} onError={() => setFailed(true)} /> : <span className="hint">{hint}</span>}
    </div>
  );
}
