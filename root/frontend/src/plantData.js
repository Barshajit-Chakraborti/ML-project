// Static plant info for the library. Photos live in public/plants/<slug>.jpg
// (run `node scripts/fetch-plant-images.mjs` once to download them).
export const PLANTS = [
  { name: "Aegle marmelos", common: "Bael", uses: ["Unripe fruit is traditionally used for diarrhoea and dysentery", "Ripe fruit is used as a cooling digestive tonic"] },
  { name: "Aloe vera", common: "Aloe vera (Ghritakumari)", uses: ["Gel is applied to burns and minor skin irritation", "Juice is traditionally used for constipation"] },
  { name: "Andrographis paniculata", common: "Kalmegh", uses: ["Traditionally used for fever and the common cold", "Bitter tonic for liver and digestion"] },
  { name: "Azadirachta indica", common: "Neem", uses: ["Leaves are used for skin problems such as boils and itching", "Twigs are used for cleaning teeth"] },
  { name: "Bacopa monnieri", common: "Brahmi", uses: ["Traditional tonic for memory and learning", "Used to calm stress and anxiety"] },
  { name: "Boerhavia diffusa", common: "Punarnava", uses: ["Root is used as a diuretic for swelling and water retention", "Used for urinary complaints"] },
  { name: "Catharanthus roseus", common: "Nayantara", uses: ["Source of vinblastine and vincristine, drugs used in cancer treatment"] },
  { name: "Centella asiatica", common: "Centella (Thankuni)", uses: ["Used to help heal wounds and repair skin", "Traditional tonic for memory and the nerves"] },
  { name: "Cissus quadrangularis", common: "Hadjod", uses: ["Traditionally used to help broken bones heal", "Used for joint pain"] },
  { name: "Clerodendrum colebrookianum", common: "Clerodendrum", uses: ["Leaf preparations are used in North-East India for high blood pressure", "Used in tribal medicine for fever and body pain"] },
  { name: "Clitoria ternatea", common: "Aparajita", uses: ["Flower tea is used as a brain and memory tonic", "Used to calm stress and support sleep"] },
  { name: "Eclipta prostrata", common: "Bhringaraj", uses: ["Used for hair fall and scalp care", "Used for liver complaints and jaundice"] },
  { name: "Eryngium foetidum", common: "Culantro", uses: ["Leaves are used for stomach ache and indigestion", "Used for fever and colds"] },
  { name: "Euphorbia neriifolia", common: "Indian spurge tree", uses: ["Leaves are used in folk medicine for cough and joint pain"] },
  { name: "Gymnema sylvestre", common: "Gurmar", uses: ["Traditionally used to help control blood sugar", "Reduces craving for sweet food"] },
  { name: "Hibiscus rosa-sinensis", common: "Hibiscus", uses: ["Flowers and leaves are used for hair fall and scalp care", "Flowers are used for cough"] },
  { name: "Houttuynia cordata", common: "Fish mint", uses: ["Used for cough and fever", "Eaten raw in North-East India to aid digestion"] },
  { name: "Hygrophila auriculata", common: "Marsh barbel (Kulekhara)", uses: ["Seeds and roots are used as a diuretic for urinary problems", "Used for joint pain and weakness"] },
  { name: "Justicia adhatoda", common: "Vasaka", uses: ["Leaf juice is used for cough, asthma and bronchitis", "Used to ease chest congestion"] },
  { name: "Kalanchoe pinnata", common: "Patharkuchi", uses: ["Leaves are traditionally used for kidney stones", "Leaf paste is applied to wounds and boils"] },
  { name: "Leucas aspera", common: "Dronapushpi", uses: ["Used for cold, cough and headache", "Leaf juice is applied for insect bites and skin problems"] },
  { name: "Mentha spp.", common: "Mint", wiki: "Mentha", uses: ["Used for indigestion and gas", "Used to relieve cold and headache"] },
  { name: "Nyctanthes arbor-tristis", common: "Shephali", uses: ["Leaf juice is used for fever", "Used for sciatica and joint pain"] },
  { name: "Ocimum tenuiflorum", common: "Tulsi", uses: ["Used for cough, cold and fever", "Used to ease stress"] },
  { name: "Piper betle", common: "Betel", uses: ["Leaves are chewed to freshen breath and aid digestion", "Leaf paste is applied to minor wounds"] },
  { name: "Psidium guajava", common: "Guava", uses: ["Leaves are used for diarrhoea", "Leaf rinse is used for toothache and mouth sores"] },
  { name: "Syzygium cumini", common: "Jamun", uses: ["Seed powder is traditionally used to manage blood sugar", "Bark is used for diarrhoea"] },
  { name: "Terminalia chebula", common: "Haritaki", uses: ["Used for constipation and digestion", "Fruit decoction is used as a gargle for mouth ulcers"] },
  { name: "Tinospora cordifolia", common: "Guduchi", uses: ["Used to build immunity and recover from fever", "Used for diabetes and joint pain"] },
  { name: "Vitex negundo", common: "Nirgundi", uses: ["Leaves are used for joint pain and swelling", "Used for headache and cough"] },
];

export const slug = (name) => name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

const BY_NAME = Object.fromEntries(PLANTS.map((p) => [p.name.toLowerCase(), p]));

export const plantInfo = (p) => BY_NAME[p.scientific_name?.trim().toLowerCase()] || {};
export const plantImage = (p) => p.image || `/plants/${slug(p.scientific_name || "")}.jpg`;
export const commonName = (p) => p.common_name || plantInfo(p).common || "";
