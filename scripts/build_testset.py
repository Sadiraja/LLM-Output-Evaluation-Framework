"""Generates data/test_set.jsonl (50 prompts: 30 factual QA, 10 JSON extraction, 10 list tasks).
The `mock` field is only used by the offline simulator; real backends ignore it."""
import json
from pathlib import Path

# (question, reference sentence, accepted answer alternatives, plausible wrong answer)
QA = [
 ("What is the capital of Australia?", "The capital of Australia is Canberra.", ["canberra"], "Sydney"),
 ("What is the chemical symbol for gold?", "The chemical symbol for gold is Au.", ["au"], "Ag"),
 ("Who wrote Pride and Prejudice?", "Pride and Prejudice was written by Jane Austen.", ["jane austen"], "Charlotte Bronte"),
 ("At what temperature in Celsius does water boil at sea level?", "Water boils at 100 degrees Celsius at sea level.", ["100"], "90"),
 ("What is the largest planet in our solar system?", "The largest planet in our solar system is Jupiter.", ["jupiter"], "Saturn"),
 ("In what year did World War II end?", "World War II ended in 1945.", ["1945"], "1939"),
 ("Approximately how fast does light travel in a vacuum, in kilometres per second?", "Light travels at about 299,792 kilometres per second.", ["299792", "300000"], "150,000"),
 ("Which organelle is known as the powerhouse of the cell?", "The mitochondrion is the powerhouse of the cell.", ["mitochondrion", "mitochondria"], "the nucleus"),
 ("What is the largest ocean on Earth?", "The largest ocean on Earth is the Pacific Ocean.", ["pacific"], "the Atlantic"),
 ("Who wrote the novel 1984?", "The novel 1984 was written by George Orwell.", ["orwell"], "Aldous Huxley"),
 ("What is the square root of 144?", "The square root of 144 is 12.", ["12"], "14"),
 ("What is the official currency of Japan?", "The official currency of Japan is the yen.", ["yen"], "the yuan"),
 ("What is the smallest prime number?", "The smallest prime number is 2.", ["2", "two"], "1"),
 ("What is the hardest naturally occurring substance?", "The hardest naturally occurring substance is diamond.", ["diamond"], "quartz"),
 ("Who painted the Mona Lisa?", "The Mona Lisa was painted by Leonardo da Vinci.", ["leonardo", "da vinci"], "Michelangelo"),
 ("How many continents are there?", "There are seven continents.", ["seven", "7"], "six"),
 ("Which gas do plants absorb from the atmosphere for photosynthesis?", "Plants absorb carbon dioxide for photosynthesis.", ["carbon dioxide", "co2"], "oxygen"),
 ("What is the capital of Canada?", "The capital of Canada is Ottawa.", ["ottawa"], "Toronto"),
 ("What is the common name for the compound H2O?", "The common name for H2O is water.", ["water"], "hydrogen peroxide"),
 ("Who was the first person to walk on the Moon?", "Neil Armstrong was the first person to walk on the Moon.", ["armstrong"], "Buzz Aldrin"),
 ("What is the longest river in Africa?", "The longest river in Africa is the Nile.", ["nile"], "the Congo"),
 ("How many bones are in the adult human body?", "The adult human body has 206 bones.", ["206"], "212"),
 ("Who developed the theory of general relativity?", "The theory of general relativity was developed by Albert Einstein.", ["einstein"], "Isaac Newton"),
 ("What is the capital of Pakistan?", "The capital of Pakistan is Islamabad.", ["islamabad"], "Karachi"),
 ("At what temperature in Fahrenheit does water freeze?", "Water freezes at 32 degrees Fahrenheit.", ["32"], "0"),
 ("Which planet is known as the Red Planet?", "Mars is known as the Red Planet.", ["mars"], "Venus"),
 ("Which language has the most native speakers worldwide?", "Mandarin Chinese has the most native speakers worldwide.", ["mandarin"], "English"),
 ("Who is commonly credited with inventing the telephone?", "Alexander Graham Bell is commonly credited with inventing the telephone.", ["graham bell", "bell"], "Thomas Edison"),
 ("What is the chemical formula of table salt?", "The chemical formula of table salt is NaCl.", ["nacl"], "KCl"),
 ("What is the tallest mountain above sea level?", "The tallest mountain above sea level is Mount Everest.", ["everest"], "K2"),
]

JSON_TEXTS = [
 ("Alice Smith, 34, lives in Lahore and works as an engineer.", dict(name="Alice Smith", age=34, city="Lahore", job="engineer")),
 ("Bilal Ahmed is a 29-year-old teacher from Karachi.", dict(name="Bilal Ahmed", age=29, city="Karachi", job="teacher")),
 ("Chen Wei, a 41-year-old nurse, currently resides in Singapore.", dict(name="Chen Wei", age=41, city="Singapore", job="nurse")),
 ("Dana Lopez (52) works as a chef in Madrid.", dict(name="Dana Lopez", age=52, city="Madrid", job="chef")),
 ("Emre Yilmaz is a 23-year-old student living in Istanbul.", dict(name="Emre Yilmaz", age=23, city="Istanbul", job="student")),
 ("Fatima Khan, 38, is a lawyer based in Islamabad.", dict(name="Fatima Khan", age=38, city="Islamabad", job="lawyer")),
 ("Grace Okafor, age 27, is a pilot who lives in Lagos.", dict(name="Grace Okafor", age=27, city="Lagos", job="pilot")),
 ("Hiro Tanaka is a 45-year-old architect from Osaka.", dict(name="Hiro Tanaka", age=45, city="Osaka", job="architect")),
 ("Ivana Petrova, 31, works as a dentist in Prague.", dict(name="Ivana Petrova", age=31, city="Prague", job="dentist")),
 ("James O'Brien, 60, is a farmer living in Galway.", dict(name="James O'Brien", age=60, city="Galway", job="farmer")),
]

# (task, [(alternatives, example bullet)...]) ; a response needs >= 3 distinct groups
LISTS = [
 ("Give exactly 3 benefits of regular exercise.", [
  (["heart", "cardio"], "Improves heart health"), (["mood", "mental", "stress"], "Boosts mood and reduces stress"),
  (["sleep"], "Helps you sleep better"), (["weight"], "Helps manage body weight"),
  (["muscle", "strength"], "Builds muscle strength"), (["energy"], "Increases daily energy")]),
 ("Give exactly 3 ways to reduce household energy use.", [
  (["led", "bulb", "lighting"], "Switch to LED bulbs"), (["thermostat", "heating"], "Lower the thermostat in winter"),
  (["insulat"], "Improve home insulation"), (["unplug", "standby"], "Unplug devices on standby"),
  (["appliance", "efficient"], "Use efficient appliances"), (["solar"], "Install solar panels")]),
 ("Give exactly 3 tips for a successful job interview.", [
  (["research"], "Research the company beforehand"), (["practice", "rehears"], "Practice common questions"),
  (["punctual", "on time", "early"], "Arrive early and be punctual"), (["question"], "Prepare questions to ask them"),
  (["dress", "attire"], "Dress appropriately"), (["eye contact"], "Maintain eye contact")]),
 ("Name exactly 3 renewable energy sources.", [
  (["solar"], "Solar power"), (["wind"], "Wind power"), (["hydro"], "Hydroelectric power"),
  (["geothermal"], "Geothermal energy"), (["biomass", "biofuel"], "Biomass energy"), (["tidal", "wave"], "Tidal energy")]),
 ("List exactly 3 common symptoms of dehydration.", [
  (["thirst"], "Increased thirst"), (["dry"], "Dry mouth or skin"), (["headache"], "Headache"),
  (["dizz"], "Dizziness"), (["fatigue", "tired"], "Fatigue"), (["urine"], "Dark urine")]),
 ("Give exactly 3 strategies for learning a new language.", [
  (["practice", "speak"], "Practice speaking regularly"), (["vocabulary", "flashcard"], "Build vocabulary with flashcards"),
  (["immers", "travel"], "Immerse yourself in the language"), (["listen", "podcast"], "Listen to podcasts"),
  (["app", "course"], "Follow a structured course"), (["read"], "Read books in the language")]),
 ("Give exactly 3 human causes of climate change.", [
  (["fossil", "carbon", "co2", "greenhouse"], "Burning fossil fuels"), (["deforest"], "Deforestation"),
  (["industr"], "Industrial emissions"), (["agricultur", "livestock", "methane"], "Livestock methane emissions"),
  (["transport"], "Transport emissions")]),
 ("Name exactly 3 programming or query languages commonly used in data work.", [
  (["python"], "Python"), (["sql"], "SQL"), (["julia"], "Julia"), (["matlab"], "MATLAB"),
  (["scala"], "Scala"), (["sas"], "SAS")]),
 ("Give exactly 3 safety tips for crossing a road.", [
  (["look"], "Look both ways first"), (["crosswalk", "zebra", "crossing"], "Use a marked crosswalk"),
  (["traffic", "signal", "light"], "Obey traffic signals"), (["distract", "phone"], "Avoid phone distractions"),
  (["listen"], "Listen for approaching vehicles"), (["stop"], "Stop at the kerb before crossing")]),
 ("Name exactly 3 healthy breakfast foods.", [
  (["oat"], "Oatmeal"), (["egg"], "Boiled eggs"), (["fruit", "banana", "berr", "apple"], "Fresh fruit"),
  (["yogurt", "yoghurt"], "Plain yogurt"), (["whole grain", "whole-grain", "toast"], "Whole-grain toast"), (["nut"], "A handful of nuts")]),
]

items = []
for i, (q, ref, alts, wrong) in enumerate(QA, 1):
    items.append(dict(id=f"qa{i:02d}", format="sentence", question=q, reference=ref,
                      must_include=[alts], match="word", mock=dict(wrong=wrong)))
for i, (text, exp) in enumerate(JSON_TEXTS, 1):
    items.append(dict(id=f"js{i:02d}", format="json",
                      question=f'Extract the person\'s name, age, city and job from this text as JSON with keys name, age, city, job: "{text}"',
                      reference=json.dumps(exp), expected_json=exp, mock={}))
for i, (q, groups) in enumerate(LISTS, 1):
    items.append(dict(id=f"ls{i:02d}", format="list3", question=q,
                      reference="; ".join(g[1] for g in groups[:3]),
                      must_include=[g[0] for g in groups], min_hits=3, match="prefix",
                      mock=dict(concepts=[g[1] for g in groups])))

out = Path(__file__).resolve().parent.parent / "data" / "test_set.jsonl"
out.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in items) + "\n")
print(f"wrote {len(items)} items to {out}")
