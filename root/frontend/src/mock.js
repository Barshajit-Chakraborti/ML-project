// Sample data so the UI works before the backend is ready (VITE_USE_MOCK=true).
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

const PLANTS = [
  {
    id: 1, scientific_name: "Ocimum tenuiflorum", common_name: "Holy basil (Tulsi)", local_name: "তুলসী",
    family: "Lamiaceae", image: null,
    description: "An aromatic shrub with oval, toothed leaves and purple-tinged flower spikes, grown near homes across Tripura.",
    parts_used: ["Leaves", "Seeds", "Roots"],
    properties: "Taste: pungent, bitter. Potency: heating.",
    uses: ["Cough and cold", "Fever", "Digestive upset"],
    habitat: "Home gardens, village courtyards and open waste ground.",
  },
  {
    id: 2, scientific_name: "Azadirachta indica", common_name: "Neem", local_name: "নিম",
    family: "Meliaceae", image: null,
    description: "A large evergreen tree with pinnate leaves and clusters of small white flowers.",
    parts_used: ["Leaves", "Bark", "Seed oil"],
    properties: "Taste: bitter, astringent. Potency: cooling.",
    uses: ["Skin conditions", "Dental care", "Bitter tonic"],
    habitat: "Roadsides, village edges and plains in all districts.",
  },
  {
    id: 3, scientific_name: "Curcuma longa", common_name: "Turmeric", local_name: "হলুদ",
    family: "Zingiberaceae", image: null,
    description: "A herb with large lance-shaped leaves growing from an orange-yellow rhizome.",
    parts_used: ["Rhizome"],
    properties: "Taste: pungent, bitter. Potency: heating.",
    uses: ["Wound care", "Digestion", "Joint stiffness"],
    habitat: "Cultivated in shaded home gardens and small farms.",
  },
];

export async function mockIdentify() {
  await wait(1200);
  const picks = [...PLANTS].sort(() => Math.random() - 0.5);
  const conf = [0.82, 0.11, 0.04];
  return {
    id: Date.now(),
    predictions: picks.map((p, i) => ({
      plant_id: p.id, scientific_name: p.scientific_name,
      common_name: p.common_name, confidence: conf[i],
    })),
  };
}

export async function mockPlants(q) {
  await wait(200);
  const s = q.toLowerCase();
  return PLANTS.filter((p) => [p.scientific_name, p.common_name, p.local_name].join(" ").toLowerCase().includes(s));
}

export async function mockPlant(id) {
  await wait(200);
  const p = PLANTS.find((x) => String(x.id) === String(id));
  if (!p) throw new Error("Plant not found.");
  return p;
}
