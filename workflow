# 🐦 Workflow pro zadávání záznamů (hobby aplikace)

## 🎯 Cíl

Navrhnout intuitivní a rychlý způsob zadávání ptáků pro hobby uživatele:

* minimum povinných polí
* srozumitelné názvy (bez zbytečně odborného jazyka)
* chyby řešit nenásilně (spíš doporučení než blokace)

Workflow je rozdělen do očíslovaných fází.

---

## 🧭 Přehled workflow (zjednodušený)

1. Otevření formuláře
2. Základní identifikace ptáka
3. Volitelné detaily
4. Rychlá kontrola
5. Uložení

---

## 1️⃣ Otevření formuláře

* tlačítko: **„➕ Přidat ptáka“**
* otevře se jednoduchý formulář (ideálně jedna stránka)

💡 Pro hobby uživatele je lepší scroll než vícekrokový wizard.

---

## 2️⃣ Základní identifikace (hlavní část)

### 🟢 Povinné:

* `nazev` → např. „Kos černý“
* `vedecky_nazev` → např. „Turdus merula“

### 🟡 Volitelné ale doporučené:

* `rad`
* `celed`

### UX:

* našeptávač (autocomplete)
* kontrola duplicity:

  * „Tento pták už možná existuje…“

---

## 3️⃣ Volitelné detaily (sbalená sekce)

👉 Sekce je defaultně sbalená, aby neodrazovala začátečníky

---

### 📏 Velikost

* `delka_cm`
* `rozpeti_cm`
* `hmotnost_g`

**UX:**

* placeholdery (např. „cca 25 cm“)
* hodnoty nemusí být přesné

---

### 🌍 Ekologie

* `vyskyt_kontinent` → multi-select
* `migrace` → toggle (ano / ne)

---

### 🍽️ Potrava

* `typ_potravy` → jednoduchý výběr:

  * hmyz
  * semena
  * maso
  * všežravec

---

### ⚠️ Ohrožení

* `status_ohrozeni` → dropdown (lidsky popsaný):

  * málo dotčený
  * téměř ohrožený
  * ohrožený
  * kriticky ohrožený

---

### 🥚 Rozmnožování

* `snuska_ks`

---

## 4️⃣ Kontrola (velmi lehká)

### ❌ Validace:

* pouze:

  * povinná pole jsou vyplněna
  * číselné hodnoty dávají smysl

### ⚠️ Warningy (neblokující):

* extrémní hodnoty
* chybějící data

💡 Uživatel může uložit i nekompletní záznam.

---

## 5️⃣ Uložení

### Tlačítka:

* 💾 **Uložit**
* 💾➕ **Uložit a přidat další**

### Po uložení:

* notifikace: „Pták uložen 🐦“
* možnosti:

  * zobrazit detail
  * upravit záznam
  * návrat na seznam

---

## 🌐 Vícejazyčnost (light verze)

### UI jazyky:

* 🇨🇿 čeština (default)
* 🇬🇧 angličtina
* 🇩🇪 němčina (nebo jiný třetí jazyk)

### Data:

* `nazev` → možnost rozšíření o překlady v budoucnu
* `vedecky_nazev` → beze změny

💡 Doporučení: začít pouze s překladem UI.

---

## ⚡ UX zásady pro hobby uživatele

* minimum povinných polí
* žádné blokující validace kromě nezbytného minima
* jednoduchý jazyk místo odborného
* použití:

  * tooltipů
  * příkladů

---

## 🔁 Rychlé přidání (bonus)

Minimalistický formulář:

* `nazev`
* `vedecky_nazev`

➡️ uloží se jako nekompletní záznam pro pozdější doplnění

---

## ⚠️ Edge cases

* duplicita:

  * nabídnout existující záznam
* chybějící vědecký název:

  * povolit, ale upozornit
* nesmyslné hodnoty:

  * uložit, ale označit jako neověřené (do budoucna)

---

## 💡 Doporučení pro backend (Flask)

* minimální backend validace
* většina UX logiky na frontendu
* povolit NULL u většiny polí
* zvážit přidání:

  * `created_at`
  * `updated_at`

---
