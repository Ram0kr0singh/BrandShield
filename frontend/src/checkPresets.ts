export type CheckPreset = {
  candidate: string;
  expected: boolean;
  label?: string;
};

type PresetSet = {
  shouldFlag: CheckPreset[];
  shouldNotFlag: CheckPreset[];
};

const curated: Record<string, PresetSet> = {
  nike: {
    shouldFlag: [
      { candidate: "N1ke", expected: true },
      { candidate: "Nkie", expected: true },
      { candidate: "Niike", expected: true },
      { candidate: "Nie", expected: true },
      { candidate: "Official Nike", expected: true },
      { candidate: "N i k e", expected: true },
      { candidate: "Nіke", label: "Nіke (Cyrillic і)", expected: true },
      { candidate: "Nike Store", expected: true },
    ],
    shouldNotFlag: [
      { candidate: "Mike's Bakery", expected: false },
      { candidate: "Nikita Sharma", expected: false },
      { candidate: "Bike Repair Shop", expected: false },
      { candidate: "Nice Shoes Outlet", expected: false },
      { candidate: "Northstar Running Club", expected: false },
      { candidate: "Niko's Pizza", expected: false },
    ],
  },
  apple: {
    shouldFlag: [
      { candidate: "App|e", expected: true },
      { candidate: "Aplpe", expected: true },
      { candidate: "Applle", expected: true },
      { candidate: "Aple", expected: true },
      { candidate: "Official Apple", expected: true },
      { candidate: "A p p l e", expected: true },
      { candidate: "Apрle", label: "Apрle (Cyrillic р)", expected: true },
      { candidate: "Apple Store", expected: true },
    ],
    shouldNotFlag: [
      { candidate: "Pineapple Cafe", expected: false },
      { candidate: "Appleton Hardware", expected: false },
      { candidate: "Applegate Legal Services", expected: false },
      { candidate: "A Place to Eat", expected: false },
      { candidate: "Maple Street Market", expected: false },
      { candidate: "A.P. Plumbing", expected: false },
    ],
  },
  samsung: {
    shouldFlag: [
      { candidate: "S4msung", expected: true },
      { candidate: "Samusng", expected: true },
      { candidate: "Samsuung", expected: true },
      { candidate: "Smsung", expected: true },
      { candidate: "Official Samsung", expected: true },
      { candidate: "S a m s u n g", expected: true },
      { candidate: "Sаmsung", label: "Sаmsung (Cyrillic а)", expected: true },
      { candidate: "Samsung Store", expected: true },
    ],
    shouldNotFlag: [
      { candidate: "Samson Plumbing", expected: false },
      { candidate: "Sam Sung Photography", expected: false },
      { candidate: "Sam's Auto Repair", expected: false },
      { candidate: "Samsara Yoga Studio", expected: false },
      { candidate: "Sam and Sons Plumbing", expected: false },
      { candidate: "Sammie Carter", expected: false },
    ],
  },
  adidas: {
    shouldFlag: [
      { candidate: "Ad1das", expected: true },
      { candidate: "Addias", expected: true },
      { candidate: "Addidas", expected: true },
      { candidate: "Adias", expected: true },
      { candidate: "Official Adidas", expected: true },
      { candidate: "A d i d a s", expected: true },
      { candidate: "Adіdas", label: "Adіdas (Cyrillic і)", expected: true },
      { candidate: "Adidas Store", expected: true },
    ],
    shouldNotFlag: [
      { candidate: "Addison Dance Studio", expected: false },
      { candidate: "Adelaide Shoe Repair", expected: false },
      { candidate: "Adler Family Dental", expected: false },
      { candidate: "A.D. Design Studio", expected: false },
      { candidate: "Adelina Sports Therapy", expected: false },
      { candidate: "David's Shoe Store", expected: false },
    ],
  },
  spotify: {
    shouldFlag: [
      { candidate: "Spot1fy", expected: true },
      { candidate: "Spoitfy", expected: true },
      { candidate: "Spottify", expected: true },
      { candidate: "Spotfy", expected: true },
      { candidate: "Official Spotify", expected: true },
      { candidate: "S p o t i f y", expected: true },
      { candidate: "Spotіfy", label: "Spotіfy (Cyrillic і)", expected: true },
      { candidate: "Spotify Store", expected: true },
    ],
    shouldNotFlag: [
      { candidate: "Spotlight Audio Rentals", expected: false },
      { candidate: "Spotless Home Cleaning", expected: false },
      { candidate: "Spotted Dog Cafe", expected: false },
      { candidate: "S. Potter Consulting", expected: false },
      { candidate: "Sporty Gifts", expected: false },
      { candidate: "Porter Family Law", expected: false },
    ],
  },
};

const homoglyphs: Record<string, string> = {
  a: "а",
  e: "е",
  o: "о",
  p: "р",
  c: "с",
  x: "х",
  y: "у",
  i: "і",
};

const confusables: Record<string, string> = {
  i: "1",
  l: "|",
  o: "0",
  e: "3",
  a: "4",
  s: "5",
};

function generatedFlagExamples(name: string): CheckPreset[] {
  const trimmed = name.trim();
  const compact = trimmed.replace(/\s+/g, "");
  if (compact.length < 3) return [];

  const substitutionIndex = [...compact.toLowerCase()].findIndex(character => character in confusables);
  const homoglyphIndex = [...compact.toLowerCase()].findIndex(character => character in homoglyphs);
  const substitution = substitutionIndex >= 0
    ? [...compact].map((character, index) => index === substitutionIndex ? confusables[character.toLowerCase()] : character).join("")
    : homoglyphIndex >= 0
      ? `${compact.slice(0, homoglyphIndex)}${homoglyphs[compact[homoglyphIndex].toLowerCase()]}${compact.slice(homoglyphIndex + 1)}`
      : null;

  let transposition: string | null = null;
  for (let index = 0; index < compact.length - 1; index += 1) {
    if (compact.length >= 4 && compact[index].toLowerCase() !== compact[index + 1].toLowerCase()) {
      transposition = `${compact.slice(0, index)}${compact[index + 1]}${compact[index]}${compact.slice(index + 2)}`;
      break;
    }
  }

  const repeatIndex = Math.max(1, Math.floor(compact.length / 2));
  const repeat = compact.length >= 4 ? `${compact.slice(0, repeatIndex)}${compact[repeatIndex]}${compact.slice(repeatIndex)}` : null;
  const omissionIndex = Math.max(1, Math.floor(compact.length / 2));
  const omission = compact.length >= 4 ? `${compact.slice(0, omissionIndex)}${compact.slice(omissionIndex + 1)}` : null;
  const flags: CheckPreset[] = [
    ...(substitution ? [{ candidate: substitution, expected: true }] : []),
    ...(transposition ? [{ candidate: transposition, expected: true }] : []),
    ...(repeat ? [{ candidate: repeat, expected: true }] : []),
    ...(omission ? [{ candidate: omission, expected: true }] : []),
    { candidate: `Official ${trimmed}`, expected: true },
    { candidate: [...compact].join(" "), expected: true },
  ];
  if (homoglyphIndex >= 0) {
    const original = compact[homoglyphIndex];
    const homoglyph = homoglyphs[original.toLowerCase()];
    const candidate = `${compact.slice(0, homoglyphIndex)}${original === original.toUpperCase() ? homoglyph.toUpperCase() : homoglyph}${compact.slice(homoglyphIndex + 1)}`;
    flags.push({ candidate, label: `${candidate} (Cyrillic ${homoglyph})`, expected: true });
  }
  flags.push({ candidate: `${trimmed} Store`, expected: true });
  return flags;
}

export function presetsForBrand(name: string): PresetSet {
  const found = curated[name.trim().toLowerCase()];
  if (found) return found;
  return {
    shouldFlag: generatedFlagExamples(name),
    shouldNotFlag: [
      { candidate: "Maple Street Market", expected: false },
      { candidate: "Jordan Lee Consulting", expected: false },
      { candidate: "Northstar Bicycle Repair", expected: false },
      { candidate: "Harborview Dental", expected: false },
      { candidate: "Pine Grove Bakery", expected: false },
      { candidate: "Cedar Valley Plumbing", expected: false },
    ],
  };
}
