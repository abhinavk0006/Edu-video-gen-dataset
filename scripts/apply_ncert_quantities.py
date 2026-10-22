"""Apply curated quantities from the user's eleven NCERT XII chemistry PDFs.

No density, drop size, vessel working capacity or missing dose is inferred.
Run from any directory; sources must already be present under --source-dir.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOLS: dict[str, list[dict]] = {}
MATERIALS = {
    "205": ["burette", "pipette", "conical flask", "0.1 M oxalic acid", "potassium permanganate", "1 M sulphuric acid", "heat source"],
    "206": ["burette", "pipette", "conical flask", "250 mL volumetric flask", "Mohr's salt", "potassium permanganate", "sulphuric acid", "water"],
    "301": ["identified unknown salt", "test tubes", "droppers", "selected branch reagents", "water", "heat source"],
    "402": ["identified organic sample", "test tubes sized for the chosen protocol", "selected functional-group reagents", "water bath"],
    "403": ["selected food or standard sample", "separate test aliquots", "test tubes sized for the chosen protocol", "selected test reagents", "water bath"],
    "501": ["chromatography paper", "developing jar", "capillary", "leaf or flower extract", "petroleum ether", "selected chloroform or acetone mobile phase"],
    "502": ["chromatography paper", "developing jar", "capillary", "lead/cadmium nitrate sample", "ethanol", "6 M nitric acid", "water", "ammonium sulphide developer"],
    "601": ["potassium sulphate", "aluminium sulphate", "ferrous sulphate", "ammonium sulphate", "dilute sulphuric acid", "water", "alcohol", "50 mL vessels", "filter"],
    "602": ["oxalic acid", "potassium hydroxide", "ferric chloride", "water", "50 mL beaker", "water bath", "filter", "alcohol"],
    "603": ["aniline", "selected acetylating reagent and solvent", "vessel appropriate to the chosen scale", "ice-cold receiving water", "filter", "recrystallisation solvent"],
    "604": ["benzaldehyde", "acetone", "sodium hydroxide", "ethanol", "water", "250 mL beaker", "stirrer", "ice bath", "filter"],
    "605": ["acetanilide", "glacial acetic acid", "concentrated nitric acid", "concentrated sulphuric acid", "100 mL beaker", "ice bath", "crushed ice", "filter", "alcohol"],
    "606": ["aniline", "concentrated hydrochloric acid", "sodium nitrite", "beta-naphthol", "10% NaOH", "water", "ice", "separate preparation and receiving beakers", "filter"],
    "801": ["selected colloid precursor", "water", "250 mL beakers", "stirrer", "heat source", "reagents for the chosen colloid only"],
    "802": ["albumin sol", "30 by 30 cm membrane", "trough", "thread", "distilled water", "separate test tubes", "uranyl zinc acetate", "silver nitrate"],
    "803": ["mustard oil", "linseed oil", "castor oil", "machine oil", "water", "soap or detergent", "test tubes", "droppers", "stopwatch"],
    "901": ["0.1 M sodium thiosulphate", "1 M hydrochloric acid", "100 mL beaker", "burette", "stopwatch", "cross-marked background", "temperature bath"],
    "902": ["0.1 M sodium thiosulphate", "1 M hydrochloric acid", "beaker", "thermometer", "temperature bath", "stopwatch", "cross-marked background"],
    "903": ["potassium iodide", "hydrogen peroxide", "sulphuric acid", "sodium thiosulphate", "fresh starch", "water", "separate stock and reaction flasks", "stopwatch"],
    "904": ["potassium iodate", "fresh sodium sulphite", "fresh starch", "sulphuric acid", "water", "250 mL flasks", "stopwatch"],
    "1001": ["potassium nitrate", "water", "calorimeter", "250 mL beakers", "500 mL insulating outer beaker", "balance", "thermometer", "stirrer"],
    "1002": ["1 M hydrochloric acid", "1 M sodium hydroxide", "calibrated calorimeter", "250 mL beaker", "thermometer", "measuring cylinders", "stirrer"],
    "1101": ["zinc electrode", "copper electrode", "1 M zinc sulphate", "separately prepared copper sulphate concentrations", "salt bridge", "voltmeter", "50 mL beakers"],
}


def q(reagent, amount=None, unit=None, *, role="addition", qualifier="exact", concentration=None, note=None):
    value = {"reagent": reagent, "role": role, "qualifier": qualifier}
    if isinstance(amount, tuple):
        value.update(minimum=amount[0], maximum=amount[1], qualifier="range")
    elif amount is not None:
        value["value"] = amount
    else:
        value["qualifier"] = "not_specified"
    if unit:
        value["unit"] = unit
    if concentration:
        value["concentration"] = concentration
    if note:
        value["note"] = note
    return value


def s(page, instruction, observation, *quantities, sample="reaction", scope="source_defined"):
    return {"instruction": instruction, "observation": observation,
            "quantities": list(quantities), "pdf_page": page, "sample_id": sample,
            "reaction_scope": scope}


def p(record, variant, file, experiment, title, steps, *, notes=None, partial=False):
    source_id = "ncert_" + file
    for i, step in enumerate(steps, 1):
        page = step.pop("pdf_page")
        step.update(step_id=i, source_evidence=[{"source_id": source_id,
                    "file": file + ".pdf", "pdf_page": page, "experiment": experiment}],
                    quantity_constraint="Use only the stated dose for this sample. Unknown doses remain unset; do not substitute equal additions or convert drops to mL.")
    PROTOCOLS.setdefault(record, []).append({"variant_id": variant, "title": title,
        "source_id": source_id, "source_experiment": experiment,
        "coverage": "partial" if partial else "transcribed",
        "sample_policy": "Independent protocol; do not concatenate with other variants. Within this protocol preserve each named sample; new aliquots/trials need separate state tracks and reference images.",
        "notes": notes or [], "procedure_steps": steps})


def curate():
    # Unit 1: different colloids have deliberately different appearances.
    for material in ("starch", "gum"):
        p("chem_12_801", material, "lelm101", "1.1(a)", material.title() + " sol", [
            s(2, "Boil 100 mL distilled water in a 250 mL beaker.", "Boiling water is initially clear.", q("water",100,"mL"),q("beaker",250,"mL",role="vessel_capacity")),
            s(2, f"Make a paste of 500 mg {material} with a little hot water; add to the boiling water while stirring.", "Dispersed material forms a sol; do not label this a true molecular solution.",q(material,500,"mg"),q("paste water")),
            s(2, "Boil with constant stirring for 10 minutes.", "The prepared sol remains dispersed.",q("stirring time",10,"min",role="condition"))])
    p("chem_12_801", "albumin", "lelm101", "1.1(a)", "Egg-albumin sol", [
        s(2,"Place 100 mL of 5% (w/v) sodium chloride solution in a 250 mL beaker.","A clear salt solution is present.",q("NaCl solution",100,"mL",concentration="5% w/v"),q("beaker",250,"mL",role="vessel_capacity")),
        s(2,"Separate the albumin of one egg and stir it into the sodium chloride solution.","Albumin is dispersed in the prepared sol.",q("egg albumin",1,"egg"))])
    for salt, colour in (("ferric chloride","brown"),("aluminium chloride","white")):
        p("chem_12_801", salt.replace(" ","_"), "lelm101", "1.1(b)", salt.title()+" hydrolysis sol", [
            s(3,f"Dissolve 2 g {salt} in 100 mL boiling water in a 250 mL beaker (water preparation begins on PDF p2).","This is a stock preparation, not an addition to the final vessel.",q(salt,2,"g",role="stock_preparation"),q("water",100,"mL",role="stock_preparation"),sample="stock"),
            s(3,"Boil another 100 mL water in a separate 250 mL beaker.","The receiving beaker contains its own water charge.",q("water",100,"mL"),q("beaker",250,"mL",role="vessel_capacity")),
            s(3,"Add 10 mL of the prepared stock drop by drop with stirring; continue boiling.",f"A {colour} hydroxide sol forms; this is not a clear dissolved salt solution.",q("stock aliquot",10,"mL"))])
    p("chem_12_801","arsenious_sulphide","lelm101","1.1(b)","Arsenious sulphide sol (historical hazardous method)",[
        s(3,"Boil 0.2 g arsenious oxide with 100 mL water; cool and filter.","The filtered preparation is used for the sol.",q("arsenious oxide",0.2,"g"),q("water",100,"mL")),
        s(3,"Pass hydrogen sulphide through the filtrate using the reviewed laboratory setup; remove excess gas by the source heating/filtering procedure.","A yellow arsenious sulphide sol forms.",q("H2S",note="Source uses an odour endpoint. Do not depict inhalation or invent a gas dose."))], partial=True,notes=["Toxic arsenic/H2S method requires domain and safety review; odour is not a visual endpoint."])
    p("chem_12_802","dialysis","lelm101","1.2","Dialysis of albumin sol",[
        s(4,"Prepare a parchment/cellophane cone from a 30 by 30 cm sheet and place albumin sol inside.","Sol is retained inside the membrane.",q("membrane side",30,"cm",role="apparatus_dimension"),q("albumin sol")),
        s(5,"Suspend the cone in distilled water and inspect the external water after half an hour; change the external water during dialysis.","Small ions diffuse into the external water; the colloid remains inside.",q("external water"),q("first inspection",30,"min",role="condition")),
        s(5,"Use separate external-water aliquots for sodium and chloride tests with uranyl zinc acetate and silver nitrate respectively.","Yellow sodium-test and white chloride-test precipitates indicate ions outside the membrane; doses are not stated.",q("test aliquots"),q("uranyl zinc acetate"),q("silver nitrate"),sample="separate_test_aliquots")])
    p("chem_12_803","oil_comparison","lelm101","1.3","Soap-stabilised oil emulsions",[
        s(6,"Prepare stock A by dissolving 1 g soap/detergent in 10 mL water; warm if needed.","Soap stock is prepared separately.",q("soap",1,"g",role="stock_preparation"),q("water",10,"mL",role="stock_preparation"),sample="stock_A"),
        s(6,"Prepare separate tubes B-E, each with 5 mL water and 10 drops of its assigned mustard, linseed, castor or machine oil.","Each labelled tube is an independent oil sample.",q("water per tube",5,"mL"),q("assigned oil per tube",10,"drops"),sample="fresh_B_to_E"),
        s(7,"Shake each tube for 5 minutes and record its separation time.","Separation times are measured, not invented.",q("shaking time",5,"min",role="condition"),sample="fresh_B_to_E"),
        s(7,"Add 2 drops stock A to each existing tube, shake for 5 minutes and compare separation times.","Soap stabilises the emulsions; preserve each tube's prior contents.",q("stock A per tube",2,"drops"),q("shaking time",5,"min",role="condition"),sample="fresh_B_to_E")])
    # Unit 2: fresh trials, not one continually filling vessel.
    for acid in (1,2,4,8,16):
        p("chem_12_901",f"hcl_{acid}ml","lelm102","2.1(A)",f"Fresh trial with {acid} mL HCl",[
            s(2,"Take a fresh 50 mL aliquot of 0.1 M sodium thiosulphate in a 100 mL beaker; keep the temperature constant.","The initial aliquot is clear.",q("sodium thiosulphate",50,"mL",concentration="0.1 M"),q("beaker",100,"mL",role="vessel_capacity")),
            s(3,f"Add {acid} mL 1 M HCl, swirl and start timing halfway through this transfer.","Sulphur formation gradually obscures the cross below the beaker.",q("HCl",acid,"mL",concentration="1 M")),
            s(3,"Stop timing when the cross disappears and record the measured elapsed time.","Compare this independent trial with the other prescribed acid volumes; do not invent a time.")])
    for temp in (30,40,50,60,70):
        p("chem_12_902",f"temperature_{temp}c","lelm102","2.1(B)",f"Fresh trial at {temp} degrees C",[
            s(3,f"Equilibrate fresh 50 mL 0.1 M thiosulphate at {temp} degrees C.","Each temperature trial starts with a fresh clear aliquot.",q("sodium thiosulphate",50,"mL",concentration="0.1 M"),q("temperature",temp,"degC",role="condition")),
            s(3,"Add 5 mL 1 M HCl, swirl and start timing halfway through transfer.","Sulphur gradually clouds the sample.",q("HCl",5,"mL",concentration="1 M")),
            s(3,"Record the time when the cross disappears.","Record measured time without fabricating a numerical result.")])
    for label,ki,water in (("B",10,80),("C",20,70),("D",30,60)):
        p("chem_12_903",f"mixture_{label.lower()}","lelm102","2.2",f"Iodide clock mixture {label}",[
            s(6,"Prepare stock A in a 500 mL flask: 25 mL 3% hydrogen peroxide, 25 mL 2.5 M sulphuric acid, 5 mL fresh starch solution and 195 mL water.","Stock A is separate from the reaction flask.",q("H2O2",25,"mL",role="stock_preparation",concentration="3% (basis not stated)"),q("H2SO4",25,"mL",role="stock_preparation",concentration="2.5 M"),q("starch solution",5,"mL",role="stock_preparation"),q("water",195,"mL",role="stock_preparation"),sample="stock_A"),
            s(7,f"Prepare stock {label} in a separate 250 mL flask: 10 mL 0.04 M thiosulphate, {ki} mL 0.1 M KI and {water} mL water.","This is a 100 mL stock mixture, not the final reaction charge.",q("thiosulphate",10,"mL",role="stock_preparation",concentration="0.04 M"),q("KI",ki,"mL",role="stock_preparation",concentration="0.1 M"),q("water",water,"mL",role="stock_preparation"),sample="stock_"+label),
            s(7,f"Combine 25 mL A with 25 mL {label} in fresh reaction flask E; stir and time from halfway through the second transfer.","Blue colour appears after the clock delay; repeat with fresh aliquots and average measured readings.",q("stock A",25,"mL"),q("stock "+label,25,"mL"))])
    for label,sulphite,water in (("B",20,75),("C",15,80),("D",10,85),("E",5,90)):
        p("chem_12_904",f"mixture_{label.lower()}","lelm102","2.3",f"Iodate clock mixture {label}",[
            s(9,"Prepare stock A: 25 mL 6% potassium iodate, 25 mL 2 M sulphuric acid and 50 mL water in a 250 mL flask.","Stock A is separate from the reaction flask.",q("KIO3",25,"mL",role="stock_preparation",concentration="6% (basis not stated)"),q("H2SO4",25,"mL",role="stock_preparation",concentration="2 M"),q("water",50,"mL",role="stock_preparation"),sample="stock_A"),
            s(9,f"Prepare stock {label}: {sulphite} mL 6% sodium sulphite, 5 mL 5% starch and {water} mL water in a separate 250 mL flask.","This stock totals 100 mL; only an aliquot enters the reaction.",q("Na2SO3",sulphite,"mL",role="stock_preparation",concentration="6% (basis not stated)"),q("starch",5,"mL",role="stock_preparation",concentration="5% (basis not stated)"),q("water",water,"mL",role="stock_preparation"),sample="stock_"+label),
            s(10,f"Combine 25 mL A and 25 mL {label} in fresh flask F; stir, time from halfway through addition and record the blue endpoint. Repeat twice with fresh aliquots.","Blue endpoint time is measured for this mixture.",q("stock A",25,"mL"),q("stock "+label,25,"mL"))])
    # Units 3-6.
    p("chem_12_1001","potassium_nitrate","lelm103","3.1","Enthalpy of dissolution of potassium nitrate",[
        s(3,"Calibrate the calorimeter separately: measure 100 mL cold water in beaker A and 100 mL hot water at 50-60 degrees C in beaker B; mix and record temperatures.","Calibration water is not retained for the dissolution run.",q("cold water",100,"mL"),q("hot water",100,"mL"),q("hot-water temperature",(50,60),"degC",role="condition"),sample="calibration"),
        s(4,"For the dissolution run place a fresh 100 mL water charge in the calibrated calorimeter and record its temperature.","The initial water charge is clear.",q("water",100,"mL")),
        s(5,"Weigh W1 grams potassium nitrate, record W1, add to the water and stir until fully dissolved; record temperature.","A clear solution forms and temperature decreases. W1 is a measured variable, not an invented fixed mass.",q("KNO3",qualifier="not_specified",note="Procedure uses measured W1; materials inventory lists 2 g but is not a required exact procedural dose."),scope="whole_contents")])
    p("chem_12_1002","neutralisation","lelm103","3.2","Neutralisation calorimetry",[
        s(7,"Use the separately calibrated calorimeter; place 100 mL 1 M HCl inside and record temperature.","The acid is a clear solution.",q("HCl",100,"mL",concentration="1 M")),
        s(7,"Measure 100 mL 1 M NaOH in a separate 250 mL beaker and record temperature.","Base is measured separately before transfer.",q("NaOH",100,"mL",concentration="1 M"),sample="base_beaker"),
        s(7,"Pour the measured base into the acid, stir and record temperature rise.","The mixed liquid stays clear; measured temperature rises.",q("prepared NaOH charge",100,"mL",role="transfer"),scope="whole_contents")],notes=["Calibrate using Experiment 3.1; calibration water is separate, not an additional reaction dose."])
    for c in (0.2,0.1,0.05,0.025,0.0125):
        p("chem_12_1101",str(c).replace(".","p")+"m_copper","lelm104","4.1",f"Cell with {c} M copper sulphate",[
            s(3,f"Set up separate zinc/1 M zinc sulphate and copper/{c} M copper sulphate half-cells with 50 mL beakers.","Two half-cells are connected through a salt bridge; copper electrolyte is blue.",q("ZnSO4",40,"mL",role="inventory",concentration="1 M",note="Materials list, not a separately specified procedural transfer."),q("CuSO4",40,"mL",role="inventory",concentration=f"{c} M"),q("beaker",50,"mL",role="vessel_capacity"),sample="two_half_cells"),
            s(3,"Measure potential and polarity with the bridge in place.","Record measured potential; do not fabricate a reading.",sample="two_half_cells"),
            s(3,"Remove the salt bridge after measurement. Replace the copper half-cell with a separately prepared concentration for the next trial.","This is a replacement beaker, not a top-up of the prior half-cell.",sample="two_half_cells")],notes=["Source conflict: materials list starts CuSO4 at 0.25 M; procedure and Table 4.1 specify 0.2 M. These variants follow procedure/table; teacher review pending."])
    for name,a,b,solvent in (("chloroform",19,1,"chloroform"),("acetone",18,2,"acetone")):
        p("chem_12_501",name,"lelm105","5.1","Pigment chromatography / "+name,[
            s(2,"Prepare a leaf/flower extract with a small amount of methanol or acetone; filter.","Pigments are extracted; solvent quantity is not stated.",q("extraction solvent"),sample="extract"),
            s(3,"Use 4 by 17 cm paper with a baseline 3 cm above the lower end; apply and dry extract spots.","The sample spot remains above the mobile phase.",q("paper width",4,"cm",role="apparatus_dimension"),q("paper length",17,"cm",role="apparatus_dimension"),q("baseline height",3,"cm",role="apparatus_dimension"),sample="paper"),
            s(3,f"Prepare mobile phase from {a} mL petroleum ether (60-80 degrees C boiling fraction) and {b} mL {solvent}; develop to about two-thirds paper length and mark the solvent front.","Separate pigment bands permit measured Rf calculation.",q("petroleum ether",a,"mL"),q(solvent,b,"mL"),sample="chamber")])
    p("chem_12_502","metal_ions","lelm105","5.2","Paper separation of lead and cadmium",[
        s(5,"Apply 1-2% lead/cadmium nitrate sample solution to 4 by 17 cm paper with baseline 3 cm from its end.","Dry sample spots are above the mobile-phase level.",q("sample concentration",(1,2),"%",role="condition",note="Percentage basis not specified."),q("sample spot dose"),sample="paper"),
        s(5,"Develop in ethanol : 6 M nitric acid : water, 8:1:1 by volume; keep solvent below the baseline.","The source specifies a ratio, not a total mobile-phase volume.",q("ethanol : 6 M HNO3 : water","8:1:1","volume_ratio",role="mixture_ratio"),sample="chamber"),
        s(5,"Mark the solvent front, dry and apply ammonium sulphide developer.","Lead gives black and cadmium yellow spots; measure distances for Rf.",q("developer dose"),sample="paper")])
    p("chem_12_205","oxalic_0p1m","lelm106","6.1","KMnO4 against 0.1 M oxalic acid",[
        s(3,"Rinse and fill the burette with permanganate; remove nozzle bubbles and note the initial upper-meniscus reading.","Burette contains the titrant; no endpoint volume is predetermined.",q("KMnO4",note="Burette charge and consumed volume are not fixed; determine by titration."),sample="burette"),
        s(3,"Pipette 10 mL 0.1 M oxalic acid into a conical flask and add about 5 mL 1 M sulphuric acid.","The initial flask liquid is clear and colourless.",q("oxalic acid",10,"mL",concentration="0.1 M"),q("H2SO4",5,"mL",qualifier="approximate",concentration="1 M")),
        s(3,"Heat to 50-60 degrees C and titrate with gentle swirling until permanent light pink; use fresh aliquots for three concordant readings.","Permanganate initially decolourises throughout the mixed contents; the endpoint is pale pink, not opaque white.",q("temperature",(50,60),"degC",role="condition"),q("KMnO4",note="Endpoint-controlled; maximum added volume not stated."),scope="whole_contents")],notes=["The old catalogue title said 0.05 M. Experiment 6.1 explicitly uses 0.1 M; do not reuse the old concentration.","Preparation of oxalic acid is cross-referenced to the Class XI manual and is not specified here."])
    p("chem_12_206","mohr_0p05m","lelm106","6.2","KMnO4 against Mohr's salt",[
        s(7,"Weigh 4.9000 g Mohr's salt, dissolve and transfer to a 250 mL volumetric flask; add dilute sulphuric acid dropwise until clear, then make up to the mark with water and mix.","Final stock volume is 250 mL, not 250 mL of added water. The stock is clear, potentially pale green.",q("Mohr's salt",4.9000,"g",role="stock_preparation"),q("dilute H2SO4",note="Dropwise until clear; dose not stated."),q("prepared stock",250,"mL",role="final_solution_volume",concentration="0.05 M"),sample="stock"),
        s(7,"Take 10 mL 0.05 M stock in a conical flask and add about 5 mL 1 M sulphuric acid.","A clear acidified aliquot is ready for titration.",q("Mohr stock",10,"mL",concentration="0.05 M"),q("H2SO4",5,"mL",qualifier="approximate",concentration="1 M")),
        s(7,"Titrate at room temperature with permanganate while swirling to permanent pale pink; repeat on fresh aliquots for concordant readings. Do not heat.","Endpoint is pale pink; volume consumed is measured.",q("KMnO4",note="Endpoint-controlled; volume not predetermined."),scope="whole_contents")])
    curate_salts()
    curate_organic()
    curate_food()


def curate_salts():
    rid="chem_12_301"
    def salt(v,title,steps,notes=None):
        p(rid,v,"lelm107","7.1",title,steps,notes=notes,partial=True)
    salt("original_solution","Original solution / water-soluble salt",[
        s(21,"Take a little salt and a few mL distilled water; shake and heat if needed until fully dissolved.","The original solution must be clear and transparent; its colour depends on the chosen salt. Do not invent a universal white solution.",q("salt"),q("water",note="A few mL; exact volume absent."),scope="whole_contents")],notes=["If insoluble, follow the manual's separate solvent trials using fresh salt. Do not pour every alternative solvent into the same tube.","The specimen 1 g in 20 mL on PDF p37 is for a particular MgSO4 example, not a universal dose."])
    salt("carbonate_extract","Sodium carbonate extract stock",[
        s(4,"Boil 1 g salt with about 3 g sodium carbonate and 15 mL water for about 10 minutes; cool and filter.","Filtrate is a stock extract for separate anion-test aliquots.",q("salt",1,"g",role="stock_preparation"),q("Na2CO3",3,"g",role="stock_preparation",qualifier="approximate"),q("water",15,"mL",role="stock_preparation"),q("boiling time",10,"min",role="condition",qualifier="approximate"),sample="extract_stock")])
    salt("chloride_silver","Chloride / silver nitrate and ammonia",[
        s(9,"Take 1 mL sodium carbonate extract as a separate chloride-test aliquot; the manual also allows a water extract.","The separate test aliquot is ready. Initial clarity/colour depend on the specified sample.",q("carbonate extract",1,"mL",role="aliquot")),
        s(9,"Acidify this chloride-test aliquot with dilute nitric acid.","The same aliquot is acidified; its dose and resulting volume are not specified.",q("dilute HNO3")),
        s(9,"Add silver nitrate solution to this acidified aliquot.","A curdy white silver chloride precipitate forms only when chloride is present.",q("AgNO3 solution"),scope="whole_contents"),
        s(10,"Add ammonium hydroxide to the same silver chloride precipitate.","Silver chloride dissolves to a clear solution when the documented chemical conditions are met; no residual white upper layer should be invented.",q("NH4OH",note="Exact dose, concentration and capacity are not specified; review required."),scope="whole_contents")],notes=["The source does not specify acid, AgNO3 or NH4OH dose volumes, test-tube capacity, safe fill or initial solid mass for this confirmation.","Do not replace this aliquot with the source's unrelated MgSO4 specimen quantities."])
    for v,title,page,instruction,obs,qs in [
        ("carbonate","Carbonate",4,"Use 0.1 g salt with dilute acid; pass evolved gas into limewater.","Carbon dioxide makes limewater milky; excess CO2 can clear it.",[q("salt",0.1,"g"),q("dilute acid"),q("limewater")]),
        ("sulphide","Sulphide / nitroprusside",4,"Make 1 mL water extract alkaline with ammonium hydroxide or sodium carbonate; add one drop sodium nitroprusside.","Purple/violet colour indicates sulphide.",[q("water extract",1,"mL",role="aliquot"),q("alkali"),q("sodium nitroprusside",1,"drops")]),
        ("sulphite","Sulphite",4,"Add barium chloride to 1 mL extract; treat the white precipitate with dilute HCl. Test a separate precipitate portion with a few drops acidified permanganate.","Barium sulphite dissolves in acid; permanganate decolourises.",[q("extract",1,"mL",role="aliquot"),q("BaCl2"),q("dilute HCl"),q("acidified KMnO4",note="Few drops; exact count absent.")]),
        ("nitrite_iodide","Nitrite / iodide-starch",4,"Add a few drops each KI and starch to 1 mL water extract and acidify with acetic acid.","Blue colour indicates a positive nitrite test.",[q("water extract",1,"mL",role="aliquot"),q("KI",note="Few drops."),q("starch",note="Few drops."),q("acetic acid")]),
        ("nitrite_azo","Nitrite / azo test",4,"Acidify 1 mL water extract with acetic acid; add 2-3 drops sulphanilic acid followed by 2-3 drops 1-naphthylamine reagent.","A red colour is a positive test.",[q("water extract",1,"mL",role="aliquot"),q("acetic acid"),q("sulphanilic acid",(2,3),"drops"),q("1-naphthylamine",(2,3),"drops")]),
        ("acetate_ferric","Acetate / ferric chloride",5,"Shake 0.1 g salt with 1-2 mL water, filter if needed; add 1-2 mL neutral ferric chloride and boil.","Deep red colour changes to a brown-red precipitate on boiling.",[q("salt",0.1,"g"),q("water",(1,2),"mL"),q("neutral FeCl3",(1,2),"mL")]),
        ("acetate_ester","Acetate / ester",5,"Heat 0.1 g salt with 1 mL ethanol and 0.2 mL concentrated sulphuric acid.","The source reports a fruity odour; this is not a visible colour change or an instruction to inhale.",[q("salt",0.1,"g"),q("ethanol",1,"mL"),q("conc H2SO4",0.2,"mL")]),
        ("bromide_layer","Bromide / layer test",9,"Neutralise 1 mL extract with HCl; add 1 mL source-approved organic solvent and excess chlorine water dropwise; shake.","Brown colour develops in the organic layer; layering is intentional.",[q("extract",1,"mL",role="aliquot"),q("HCl"),q("organic solvent",1,"mL"),q("chlorine water",note="Endpoint/excess; no fixed volume.")]),
        ("iodide_layer","Iodide / layer test",9,"Use 1 mL salt solution neutralised with HCl; add 1 mL source-approved organic solvent and excess chlorine water dropwise; shake.","Violet colour develops in the organic layer; do not homogenise the final layers.",[q("salt solution",1,"mL",role="aliquot"),q("HCl"),q("organic solvent",1,"mL"),q("chlorine water")]),
        ("nitrate_ring","Nitrate / brown-ring test",10,"To 1 mL aqueous salt solution add 2 mL concentrated sulphuric acid; mix, cool under the tap, then introduce fresh ferrous sulphate down the wall without shaking.","A brown ring forms at the interface; a layered endpoint is required.",[q("salt solution",1,"mL",role="aliquot"),q("conc H2SO4",2,"mL"),q("fresh FeSO4")]),
        ("oxalate","Oxalate",10,"Acidify 1 mL extract with acetic acid; add calcium chloride. Isolate the precipitate, dissolve in dilute sulphuric acid, add very dilute permanganate and warm.","White calcium oxalate forms; subsequent permanganate loses colour and evolved CO2 makes limewater milky.",[q("extract",1,"mL",role="aliquot"),q("acetic acid"),q("CaCl2"),q("dil H2SO4"),q("dil KMnO4")]),
        ("sulphate","Sulphate",14,"Acidify 1 mL water/carbonate extract with dilute HCl and add barium chloride.","White barium sulphate precipitate is insoluble in concentrated HCl or HNO3.",[q("extract",1,"mL",role="aliquot"),q("dil HCl"),q("BaCl2")]),
        ("phosphate","Phosphate",14,"Acidify a separate extract aliquot with concentrated nitric acid; add ammonium molybdate and heat to boiling.","Canary-yellow precipitate indicates phosphate.",[q("extract aliquot"),q("conc HNO3"),q("ammonium molybdate")]),
        ("ammonium","Ammonium",21,"Heat 0.1 g salt with 1-2 mL NaOH. Hold an HCl-moistened glass rod near the mouth; use a separate gas receiver for a Nessler test if selected.","HCl rod produces white fumes; Nessler reagent gives brown colour/precipitate in its receiver. Do not colour the parent liquid blue.",[q("salt",0.1,"g"),q("NaOH solution",(1,2),"mL"),q("HCl on rod"),q("Nessler reagent")]),
        ("dry_heating","Preliminary dry heating",16,"Heat about 0.1 g dry salt for about one minute; compare hot and cold residue.","Colour depends on the salt and is preliminary evidence only.",[q("salt",0.1,"g",qualifier="approximate"),q("heating time",1,"min",role="condition",qualifier="approximate")]),
        ("flame","Flame test",16,"Clean the platinum loop; make a small salt paste with 2-3 drops concentrated HCl and introduce the loaded loop into the flame.","Characteristic flame colour depends on the cation; this is not a solution colour change.",[q("salt"),q("conc HCl",(2,3),"drops")]),
        ("charcoal","Charcoal cavity",19,"Use a fresh charcoal cavity with about 0.2 g salt and about 0.5 g anhydrous sodium carbonate; moisten with 1-2 drops water and heat as prescribed.","Residue/bead colour depends on the cation and whether hot or cold.",[q("salt",0.2,"g",qualifier="approximate"),q("Na2CO3",0.5,"g",qualifier="approximate"),q("water",(1,2),"drops")]),
        ("cobalt_nitrate","Cobalt nitrate residue test",20,"For a white charcoal-test residue add 2-3 drops cobalt nitrate solution and heat as prescribed.","Zn/Al/Mg residues give distinct colours; do not assert one universal outcome.",[q("cobalt nitrate",(2,3),"drops")]),
    ]:
        salt(v,title,[s(page,instruction,obs,*qs,scope="interface" if v=="nitrate_ring" else "stratified" if "layer" in v else "source_defined")])
    for ion,colour in (("bromide","pale yellow; dissolves with difficulty in ammonia"),("iodide","yellow; insoluble in ammonia")):
        salt(ion+"_silver",ion.title()+" / silver salt",[s(9,"Acidify a fresh 1 mL extract aliquot with dilute nitric acid, add silver nitrate and examine solubility in ammonium hydroxide.","Positive precipitate: "+colour+".",q("extract",1,"mL",role="aliquot"),q("dil HNO3"),q("AgNO3"),q("NH4OH"))])
    # Cation confirmation branches retain unspecified doses rather than inventing mL.
    cations=[
        ("lead",23,"Dissolve the group-I precipitate in hot water; divide into separate portions for KI, potassium chromate, and alcohol/dilute sulphuric acid tests.","KI and chromate produce yellow precipitates; sulphate is white.",["hot water","KI","potassium chromate","alcohol","dil H2SO4"]),
        ("copper",25,"Use the reviewed group-IIA copper solution; add excess ammonium hydroxide, then acidify with acetic acid and add potassium ferrocyanide.","Deep-blue ammonia complex precedes chocolate-brown ferrocyanide precipitate.",["NH4OH","acetic acid","potassium ferrocyanide"]),
        ("arsenic",25,"Use the reviewed group-IIB branch: acidify yellow ammonium-sulphide solution with dilute HCl; dissolve the precipitate in hot concentrated nitric acid and add ammonium molybdate.","Yellow sulphide and subsequently canary-yellow molybdate support the selected arsenic branch.",["dil HCl","conc HNO3","ammonium molybdate"]),
        ("iron",27,"Dissolve group-III brown precipitate in dilute HCl; split into separate portions for potassium ferrocyanide and potassium thiocyanate.","Separate tests give Prussian blue and blood-red colours respectively.",["dil HCl","potassium ferrocyanide","potassium thiocyanate"]),
        ("aluminium",27,"Dissolve group-III white precipitate in dilute HCl; split for NaOH solubility and litmus/ammonium-hydroxide lake tests.","NaOH precipitate dissolves in excess; lake test has a blue floating mass in colourless solution.",["dil HCl","NaOH","blue litmus solution","NH4OH"]),
        ("zinc",29,"Dissolve the group-IV white precipitate in hot dilute HCl; split for excess NaOH and, separately, NH4OH neutralisation followed by potassium ferrocyanide.","White hydroxide dissolves in excess NaOH; separate ferrocyanide test gives bluish-white precipitate.",["dil HCl","NaOH","NH4OH","potassium ferrocyanide"]),
        ("manganese",29,"Dissolve the group-IV flesh-coloured precipitate in hot dilute HCl and add excess NaOH.","White hydroxide becomes brown on standing.",["dil HCl","NaOH"]),
        ("nickel",29,"Use the source-prepared group-IV solution; make alkaline with ammonium hydroxide and add a few drops dimethylglyoxime.","Bright-red precipitate confirms the selected nickel branch.",["NH4OH","dimethylglyoxime"]),
        ("cobalt",29,"Use a separate portion of group-IV solution; neutralise with ammonium hydroxide, acidify with dilute acetic acid and add solid potassium nitrite.","Yellow precipitate confirms the selected cobalt branch.",["NH4OH","acetic acid","potassium nitrite"]),
        ("barium",31,"Dissolve group-V carbonate in hot dilute acetic acid; use a separate portion with potassium chromate.","Yellow precipitate supports barium; grassy-green flame is a separate confirmation.",["dil acetic acid","potassium chromate"]),
        ("strontium",31,"With barium absent, add ammonium sulphate to a separate group-V solution portion; heat, scratch and cool.","White sulphate precipitate supports strontium; crimson flame is separate.",["ammonium sulphate"]),
        ("calcium",31,"With barium and strontium absent, add ammonium oxalate to a separate group-V solution portion and shake.","White calcium oxalate precipitate forms; brick-red flame is separate.",["ammonium oxalate"]),
        ("magnesium",33,"With group V absent, add disodium hydrogenphosphate to the ammoniacal original-solution aliquot, scratch the tube and warm if delayed.","White crystalline magnesium ammonium phosphate precipitates.",["original solution aliquot","disodium hydrogenphosphate"]),
    ]
    for ion,page,instr,obs,reagents in cations:
        salt("cation_"+ion,ion.title()+" confirmation (requires prior group separation)",[s(page,instr,obs,*[q(r) for r in reagents])],notes=["Partial confirmation branch; preceding group separation and sample allocation must be selected and reviewed. No numeric doses given for these additions."])


def curate_organic():
    # Unit 9: crystallisation and separate preparation variants.
    p("chem_12_601","potash_alum","lelm109","9.1(a)","Potash alum",[
        s(1,"In a 50 mL beaker heat 10 mL water to about 40 degrees C; dissolve 6.6 g aluminium sulphate and add about 0.4 mL dilute sulphuric acid.","Dissolved reagents form the crystallisation solution.",q("water",10,"mL"),q("aluminium sulphate",6.6,"g"),q("dil H2SO4",0.4,"mL",qualifier="approximate"),q("beaker",50,"mL",role="vessel_capacity")),
        s(2,"Add 2.4 g potassium sulphate, heat and stir until dissolved; cool slowly to room temperature.","White alum crystals form during cooling.",q("K2SO4",2.4,"g")),
        s(2,"Filter crystals, wash with cold water/alcohol 1:1 mixture and dry.","Crystals remain on the filter; wash-liquid volume is not specified.",q("water : alcohol","1:1","volume_ratio",role="mixture_ratio"),q("wash mixture"))],notes=["Use step-specific about 0.4 mL acid; the general introduction mentions 2-3 mL at unspecified scale."])
    p("chem_12_601","mohr_crystals","lelm109","9.1(b)","Mohr's salt crystals",[
        s(2,"Heat 3.5 g ferrous sulphate and 1.7 g ammonium sulphate in 5 mL water in a 50 mL flask; add about 0.5 mL dilute sulphuric acid.","A crystallisation solution is prepared.",q("ferrous sulphate",3.5,"g"),q("ammonium sulphate",1.7,"g"),q("water",5,"mL"),q("dil H2SO4",0.5,"mL",qualifier="approximate")),
        s(2,"Concentrate to the crystallisation point and cool slowly to room temperature.","Light-green crystals form; evaporation reduces liquid, it is not a continuity reset."),
        s(2,"Filter and wash with a small amount of cold 1:1 water/alcohol, then alcohol; dry.","Wash quantities are unspecified.",q("water : alcohol","1:1","volume_ratio",role="mixture_ratio"),q("wash liquid"))])
    p("chem_12_602","ferrioxalate","lelm109","9.2","Potassium trioxalatoferrate(III)",[
        s(3,"Dissolve 3 g oxalic acid in 12.5 mL hot water in a 50 mL beaker.","The starting solution is homogeneous.",q("oxalic acid",3,"g"),q("water",12.5,"mL")),
        s(3,"Add 3.8 g potassium hydroxide gradually with stirring, then 2.5 g ferric chloride and stir until fully dissolved.","A green solution forms throughout the mixed contents.",q("KOH",3.8,"g"),q("FeCl3",2.5,"g"),scope="whole_contents"),
        s(3,"Filter, concentrate the green filtrate on a water bath, cool slowly, wash crystals with 1:1 water/alcohol and dry.","Green crystals are isolated; wash amount is unstated.",q("water : alcohol","1:1","volume_ratio",role="mixture_ratio"),q("wash mixture"))])
    p("chem_12_603","anhydride","lelm110","10.1","Acetanilide / anhydride method",[
        s(2,"Place 5 mL aniline in a 100 mL round-bottom flask; add 5 mL acetic anhydride and 5 mL glacial acetic acid.","This selects the anhydride method, not the acetyl-chloride alternative.",q("aniline",5,"mL"),q("acetic anhydride",5,"mL"),q("glacial acetic acid",5,"mL")),
        s(2,"Add pumice, fit air condenser and reflux on a sand bath for 10-15 minutes; cool.","Reaction time is a process condition, not the generated clip duration.",q("reflux time",(10,15),"min",role="condition")),
        s(2,"Pour the cooled reaction mixture into 150-200 mL ice-cold water in a 250 mL beaker while stirring; filter, wash and recrystallise.","White acetanilide precipitates in the receiving beaker; do not add 200 mL water to the 100 mL flask.",q("receiving water",(150,200),"mL"),q("receiving beaker",250,"mL",role="vessel_capacity"),q("recrystallisation solvent",note="Small hot-water portion plus few drops alcohol."),sample="receiving_beaker")])
    p("chem_12_603","acetyl_chloride_pyridine","lelm110","10.1","Acetanilide / acetyl chloride and pyridine",[
        s(2,"For this alternative use 5 mL aniline, 5 mL acetyl chloride and 5 mL dry pyridine, replacing the anhydride/acetic-acid pair.","Mutually exclusive reagent alternatives are not combined.",q("aniline",5,"mL"),q("acetyl chloride",5,"mL"),q("dry pyridine",5,"mL")),
        s(2,"Follow the source reflux/cooling procedure for 10-15 minutes.","Process duration must be represented explicitly.",q("reflux time",(10,15),"min",role="condition")),
        s(2,"Transfer into 150-200 mL ice-cold water in a 250 mL receiving beaker; isolate, wash and recrystallise.","Solid product forms in a larger receiving vessel.",q("receiving water",(150,200),"mL"),q("receiving beaker",250,"mL",role="vessel_capacity"),sample="receiving_beaker")])
    p("chem_12_603","small_scale_alternative","lelm110","10.1 alternative","Acetanilide / small-scale source alternative",[
        s(3,"In a dry boiling tube mix 1 mL aniline and 1 mL glacial acetic acid.","This is a separate small-scale preparation.",q("aniline",1,"mL"),q("glacial acetic acid",1,"mL")),
        s(3,"Add a total of 1 mL acetyl chloride in portions of about 0.3 mL, respecting the 1 mL total; heat on a boiling-water bath for 5 minutes and cool.","Do not repeat four full 0.3 mL doses; the final portion is the remaining amount.",q("acetyl chloride total",1,"mL"),q("acetyl chloride portion",0.3,"mL",qualifier="approximate",role="portion_limit"),q("heating time",5,"min",role="condition")),
        s(3,"Add about 10 mL ice-cold water, stir, filter, wash neutral and recrystallise.","White acetanilide is isolated.",q("ice-cold water",10,"mL",qualifier="approximate"))])
    p("chem_12_604","dibenzalacetone","lelm110","10.2","Dibenzalacetone",[
        s(4,"Dissolve 3.15 g NaOH in 25 mL ethanol and 30 mL water in a 250 mL beaker; cool to 20-25 degrees C.","The alkaline mixture is prepared before carbonyl addition.",q("NaOH",3.15,"g"),q("ethanol",25,"mL"),q("water",30,"mL"),q("temperature",(20,25),"degC",role="condition")),
        s(4,"Separately mix 3.2 mL benzaldehyde and 2.3 mL acetone; add half this mixture slowly with vigorous stirring, then stir 15 minutes.","Fluffy precipitate begins in 1-2 minutes; preserve the unused half separately.",q("benzaldehyde",3.2,"mL",role="stock_preparation"),q("acetone",2.3,"mL",role="stock_preparation"),q("carbonyl mixture",0.5,"fraction_of_prepared_stock",role="transfer"),q("stirring time",15,"min",role="condition")),
        s(4,"Add the remaining half and stir 30 minutes; filter, wash cold and recrystallise from a small solvent portion.","Pale-yellow dibenzalacetone is isolated.",q("remaining stock",0.5,"fraction_of_prepared_stock",role="transfer"),q("stirring time",30,"min",role="condition"),q("recrystallisation solvent"))])
    p("chem_12_605","nitration","lelm110","10.3","p-Nitroacetanilide",[
        s(5,"Dissolve 2 g acetanilide in 2 mL glacial acetic acid in a 100 mL beaker; add 4 mL concentrated sulphuric acid gradually with stirring and cool to 0-5 degrees C.","A hot clear solution forms before chilling.",q("acetanilide",2,"g"),q("glacial acetic acid",2,"mL"),q("conc H2SO4",4,"mL"),q("cooling temperature",(0,5),"degC",role="condition")),
        s(5,"Add a cold mixture of 1.0 mL concentrated nitric acid and 1.0 mL concentrated sulphuric acid dropwise with stirring; keep below 10 degrees C.","The dose is a separate nitrating mixture; do not add another full 5 mL sulphuric acid charge.",q("conc HNO3",1,"mL"),q("conc H2SO4",1,"mL"),q("maximum temperature",10,"degC",role="upper_limit")),
        s(5,"Allow room temperature, stand about 30 minutes, then pour with stirring onto 100 g crushed ice; filter, wash, dry and recrystallise.","Product is isolated; recrystallised p-nitroacetanilide is colourless.",q("standing time",30,"min",qualifier="approximate",role="condition"),q("crushed ice",100,"g"),q("recrystallisation alcohol"),sample="ice_receiver")],notes=["Source discrepancy: materials list gives 1.5 mL HNO3; numbered procedure specifies 1.0 mL. This transcription follows procedure and remains under review."])
    p("chem_12_606","azo_coupling","lelm110","10.4","Phenyl-azo-beta-naphthol",[
        s(7,"Combine 6.5 mL concentrated HCl, 6.5 mL water and 2 mL aniline as specified; cool to 0-5 degrees C.","Diazotisation uses a chilled aniline preparation.",q("conc HCl",6.5,"mL"),q("water",6.5,"mL"),q("aniline",2,"mL"),q("temperature",(0,5),"degC",role="condition"),sample="diazonium"),
        s(7,"Prepare 1.6 g sodium nitrite in 8 mL water and add to the chilled aniline preparation.","The diazonium preparation remains cold.",q("NaNO2",1.6,"g"),q("water",8,"mL"),sample="diazonium"),
        s(8,"Separately dissolve 3.2 g beta-naphthol in 18 mL 10% NaOH and add about 25 g crushed ice.","This is a separate cold alkaline receiving mixture.",q("beta-naphthol",3.2,"g"),q("NaOH solution",18,"mL",concentration="10% (basis not stated)"),q("ice",25,"g",qualifier="approximate"),sample="coupling_receiver"),
        s(8,"Add the chilled diazonium preparation to the cold alkaline beta-naphthol, maintaining the source direction; stand in ice for 30 minutes with occasional shaking, then isolate and recrystallise about a quarter of the product.","Orange-red azo product forms.",q("standing time",30,"min",role="condition"),q("product portion",0.25,"fraction_of_product",role="recrystallisation"),q("glacial acetic acid"),sample="coupling_receiver")])
    curate_functional()


def curate_functional():
    rid="chem_12_402"
    def f(v,title,page,instr,obs,*qs,scope="source_defined"):
        p(rid,v,"lelm108","8.1",title,[s(page,instr,obs,*qs,scope=scope)],partial=True,
          notes=["Choose the analyte and this test branch explicitly. Positive outcomes are conditional; use a fresh aliquot, not one tube for every functional-group test."])
    f("bromine","Unsaturation / bromine",2,"Dissolve 0.1 g solid OR 5 drops liquid sample in 2 mL source-approved solvent; add 2% bromine solution dropwise with shaking.","Decolourisation supports unsaturation, subject to the source's interference checks.",q("solid sample",0.1,"g",role="alternative"),q("liquid sample",5,"drops",role="alternative"),q("solvent",2,"mL"),q("bromine",concentration="2% (basis not stated)"))
    f("baeyer","Unsaturation / Baeyer",2,"Use 25-30 mg sample in 2 mL water or alcohol-free acetone; add alkaline permanganate prepared from equal volumes 1% KMnO4 and 1% sodium carbonate.","Discharge of more than one drop supports unsaturation; both source unsaturation tests are needed.",q("sample",(25,30),"mg"),q("solvent",2,"mL"),q("KMnO4 : Na2CO3","1:1","volume_ratio",role="mixture_ratio",concentration="1% each, basis not stated"),q("alkaline permanganate"))
    f("ceric","Alcohol / ceric ammonium nitrate",4,"Add a few drops ceric ammonium nitrate reagent to 1 mL compound solution.","Red colour can be transient and disappears with excess reagent.",q("sample solution",1,"mL",role="aliquot"),q("ceric reagent",note="Few drops, not an exact count."))
    f("iodoform_hypochlorite","Iodoform / hypochlorite test",4,"To 0.2 mL compound add 10 mL 10% KI and 10 mL fresh sodium hypochlorite; warm.","Yellow iodoform crystals indicate a compatible analyte; do not assert all alcohols test positive.",q("compound",0.2,"mL"),q("KI solution",10,"mL",concentration="10% (basis not stated)"),q("fresh NaOCl",10,"mL"))
    f("iodoform_iodine","Iodoform / iodine-alkali test",4,"Use 0.1 g solid OR 4-5 drops liquid in 2 mL water; add dioxane dropwise only if needed for homogeneity. Add 2 mL 5% NaOH, then iodine/KI reagent to a persistent dark colour. Follow source heating/endpoint sequence; remove excess iodine with a few drops NaOH, dilute with an equal volume of water and stand 10-15 minutes.","Yellow iodoform precipitate is conditional on the analyte. Equal-volume dilution is relative to the current mixture, not a guessed fixed mL dose.",q("solid sample",0.1,"g",role="alternative"),q("liquid sample",(4,5),"drops",role="alternative"),q("water",2,"mL"),q("NaOH solution",2,"mL",concentration="5% (basis not stated)"),q("iodine/KI",note="Persistent iodine endpoint; no fixed amount."),q("dilution water",1,"current_mixture_volume",role="relative_dilution"),q("standing time",(10,15),"min",role="condition"))
    f("lucas","Alcohol / Lucas",5,"Mix 1 mL compound with 10 mL Lucas reagent and shake; observe the time of layer/turbidity formation.","Tertiary is immediate, secondary about 1-5 minutes, primary slow under source conditions; phase separation is intentional.",q("compound",1,"mL"),q("Lucas reagent",10,"mL"),scope="stratified")
    f("phenol_ferric","Phenol / ferric chloride",6,"Add neutral ferric chloride dropwise to 2 mL aqueous or alcoholic sample solution.","Blue, green, violet or red depends on the phenol; do not hard-code one universal colour.",q("sample solution",2,"mL"),q("neutral FeCl3"))
    f("phthalein","Phenol / phthalein",6,"Heat 0.1 g sample with 0.1 g phthalic anhydride and 1-2 drops concentrated sulphuric acid in an oil bath for about one minute; cool and transfer into a separate beaker containing 15 mL dilute NaOH.","Dye colour depends on compound; excess base can fade the colour.",q("sample",0.1,"g"),q("phthalic anhydride",0.1,"g"),q("conc H2SO4",(1,2),"drops"),q("receiving dilute NaOH",15,"mL"))
    f("dnp","Carbonyl / 2,4-DNP",9,"Dissolve 2-3 drops liquid OR a few crystals solid in 2-3 mL alcohol; add a few drops alcoholic DNP reagent. If needed warm on a water bath and cool.","Yellow/orange/orange-red precipitate supports carbonyl; result depends on sample.",q("liquid sample",(2,3),"drops",role="alternative"),q("solid sample",role="alternative"),q("alcohol",(2,3),"mL"),q("DNP reagent"))
    f("schiff","Aldehyde / Schiff",9,"Use 3-4 drops liquid or a few solid crystals dissolved in alcohol; add 2-3 drops Schiff reagent.","Pink colour supports an aldehyde under the source conditions.",q("liquid sample",(3,4),"drops",role="alternative"),q("solid sample",role="alternative"),q("alcohol"),q("Schiff reagent",(2,3),"drops"))
    f("fehling","Aldehyde / Fehling",9,"Mix about 1 mL each Fehling A and B; add 2-3 drops liquid OR about 2 mL solid-sample solution and heat on a water bath for about two minutes.","Brick-red precipitate is positive; aromatic aldehydes may not respond.",q("Fehling A",1,"mL",qualifier="approximate"),q("Fehling B",1,"mL",qualifier="approximate"),q("liquid sample",(2,3),"drops",role="alternative"),q("solid-sample solution",2,"mL",role="alternative",qualifier="approximate"))
    f("benedict","Aldehyde / Benedict",10,"Add 5 drops compound/solution to 2 mL Benedict reagent; heat in boiling water for five minutes.","Orange-red precipitate is a positive result for a responsive sample.",q("sample",5,"drops"),q("Benedict reagent",2,"mL"),q("heating time",5,"min",role="condition"))
    f("tollens","Aldehyde / Tollens",10,"Prepare fresh reagent from 1 mL about 2% silver nitrate and 1-2 drops NaOH; dissolve the oxide with ammonia dropwise, add sample solution and warm on a water bath for about five minutes; no direct flame.","A silver mirror supports an aldehyde; silver belongs on the glass surface.",q("AgNO3",1,"mL",concentration="about 2%, basis not stated"),q("NaOH",(1,2),"drops"),q("NH4OH",note="Until precipitate dissolves; no fixed amount."),q("sample solution"),scope="localized")
    f("carboxyl_litmus","Carboxyl / litmus",11,"Use a glass rod to place one drop compound/solution on moist blue litmus paper.","The paper turns red; do not turn the parent sample red.",q("sample",1,"drops"),scope="localized")
    f("bicarbonate","Carboxyl / bicarbonate",11,"Add a few drops liquid compound OR a few solid crystals to 2 mL saturated sodium bicarbonate.","Effervescence indicates CO2 release for a responsive acid.",q("saturated NaHCO3",2,"mL"),q("sample"))
    f("ester","Carboxyl / ester",11,"Heat about 0.1 g sample with 1 mL ethanol/methanol and 2-3 drops concentrated sulphuric acid on a 50 degrees C water bath for 10-15 minutes; pour into sodium carbonate solution.","The source's odour result is nonvisual; do not invent a colour change.",q("sample",0.1,"g",qualifier="approximate"),q("alcohol",1,"mL"),q("conc H2SO4",(2,3),"drops"),q("Na2CO3 receiver"),q("water bath",50,"degC",role="condition"),q("heating time",(10,15),"min",role="condition"))
    f("amine_solubility","Amine / acid solubility",13,"Shake 1 mL compound with a few drops dilute hydrochloric acid.","Solubility change is conditional on the selected compound.",q("compound",1,"mL"),q("dil HCl",note="Few drops."))
    f("carbylamine","Primary amine / carbylamine (historical method)",13,"The source uses 2-3 drops compound, 2-3 drops chloroform and an equal volume of 0.5 M alcoholic KOH with gentle heating; use only after specialist review.","The source reports an offensive odour, not a visible colour change. Do not depict inhalation or assume a positive test for every amine.",q("compound",(2,3),"drops"),q("chloroform",(2,3),"drops"),q("alcoholic KOH",concentration="0.5 M",note="Source says equal volume; resolve the comparison and total before numeric planning."))
    f("amine_azo","Amine / azo dye",13,"Dissolve about 0.2 g compound in 2 mL dilute HCl and cool below 5 degrees C; add 2 mL cold 2.5% sodium nitrite. Separately dissolve 0.2 g beta-naphthol in NaOH; slowly add cold diazonium solution to this receiver with shaking.","Scarlet-red dye is conditional on a suitable aromatic primary amine.",q("compound",0.2,"g",qualifier="approximate"),q("dil HCl",2,"mL"),q("NaNO2",2,"mL",concentration="2.5% (basis not stated)"),q("beta-naphthol",0.2,"g"),q("NaOH"))


def curate_food():
    def food(v,title,page,instr,obs,*qs,scope="source_defined"):
        p("chem_12_403",v,"lelm111","11.1",title,[s(page,instr,obs,*qs,scope=scope)],partial=True,
          notes=["Use a fresh aliquot for each test. Positive result depends on food/analyte identity, not just reagent addition.","Where food preparation is needed: milk uses 0.5 mL per test; flour/rice/legume extraction uses 100 mg with 10 mL water and boiling (PDF p10). Do not substitute these doses for standard-sugar aliquots."])
    food("milk_aliquot","Food preparation / milk aliquot",10,"Allocate a fresh 0.5 mL milk sample for each selected food test; apply only that test's reviewed reagent protocol.","Each test starts from a separate milk aliquot; do not accumulate all test reagents in one sample.",q("milk per test",0.5,"mL",role="aliquot"))
    food("powder_extract","Food preparation / flour, rice or legume",10,"Boil 100 mg selected wheat flour, rice, gram flour or legume powder in 10 mL distilled water; allocate separate portions for the selected tests.","This preparation is colloidal; do not assert a clear molecular solution or assume all tests are positive.",q("selected food powder",100,"mg",role="stock_preparation"),q("water",10,"mL",role="stock_preparation"),q("each test aliquot"))
    food("molisch","Carbohydrate / Molisch",2,"Use a fresh aliquot of the separately prepared 1% sugar sample (aliquot volume unstated); add 2-3 drops 1% alcoholic 1-naphthol, then 2 mL concentrated sulphuric acid carefully down the wall to form a lower layer.","A purple ring appears at the interface for a positive test; do not homogenise the endpoint.",q("1% sugar aliquot",concentration="1% (basis not stated)"),q("1-naphthol",(2,3),"drops",concentration="1% alcoholic"),q("conc H2SO4",2,"mL"),scope="interface")
    food("fehling","Reducing sugar / Fehling",4,"Add freshly mixed 1 mL Fehling A and 1 mL Fehling B to a fresh sugar aliquot and heat on a water bath.","Orange-red precipitate is positive for reducing sugars; sucrose is negative before hydrolysis.",q("sugar aliquot"),q("Fehling A",1,"mL"),q("Fehling B",1,"mL"))
    food("benedict","Reducing sugar / Benedict",4,"Add 1 mL Benedict reagent to a fresh sugar aliquot; heat in boiling water for two minutes.","Orange-red precipitate is conditional on a reducing sugar.",q("sugar aliquot"),q("Benedict reagent",1,"mL"),q("heating time",2,"min",role="condition"))
    food("tollens","Reducing sugar / Tollens",5,"Prepare fresh reagent from 1 mL aqueous silver nitrate: add NaOH dropwise to form oxide and ammonia until it dissolves; add fresh sugar aliquot and warm on water bath without direct flame.","A silver mirror is a positive reducing-sugar result on the glass surface.",q("AgNO3",1,"mL"),q("NaOH"),q("NH4OH"),q("sugar aliquot"),scope="localized")
    food("barfoed","Monosaccharide / Barfoed",5,"Use 10 drops 1% sugar solution and 1 mL Barfoed reagent; heat in boiling water for five minutes.","A red precipitate within the specified interval supports monosaccharide; prolonged heating can produce misleading disaccharide results.",q("sugar solution",10,"drops",concentration="1% (basis not stated)"),q("Barfoed reagent",1,"mL"),q("heating time",5,"min",role="condition"))
    food("sucrose_hydrolysis","Sucrose hydrolysis",6,"Heat 5 mL 1% sucrose with 5 drops concentrated HCl on a boiling-water bath; cool and add NaOH until neutral/slightly alkaline. Use separate aliquots for subsequent reducing-sugar tests.","Hydrolysed sucrose gives the source's reducing-sugar response; neutralisation dose is not fixed.",q("sucrose",5,"mL",concentration="1% (basis not stated)"),q("conc HCl",5,"drops"),q("NaOH",note="Neutral/slightly alkaline endpoint; no volume given."))
    food("seliwanoff","Sugar / Seliwanoff",7,"Mix 10 drops 1% sugar with 2 mL Seliwanoff reagent; heat in boiling water for two minutes.","Ketohexoses give red, ketopentoses blue-green; aldoses show no colour within two minutes.",q("sugar",10,"drops",concentration="1% (basis not stated)"),q("Seliwanoff reagent",2,"mL"),q("heating time",2,"min",role="condition"))
    food("starch_iodine","Starch / iodine",7,"Make a paste of 0.5 g starch with 5 mL water, disperse into 50 mL boiling water, then use a few drops iodine on a test portion.","Starch is colloidal; iodine gives blue. Do not assert the starch dispersion is a true clear solution.",q("starch",0.5,"g",role="stock_preparation"),q("paste water",5,"mL",role="stock_preparation"),q("boiling water",50,"mL",role="stock_preparation"),q("test portion"),q("iodine",note="Few drops."))
    food("fat_acrolein","Fat / acrolein (historical method)",8,"Gently heat 3 mL mustard oil/ghee with 0.5 g dry potassium hydrogen sulphate using the reviewed laboratory setup.","The source reports an irritating odour, a nonvisual endpoint; do not depict direct inhalation.",q("oil or ghee",3,"mL"),q("dry KHSO4",0.5,"g"))
    food("biuret","Protein / biuret",10,"Prepare 0.5% (w/v) casein/albumin in 0.1 M NaOH; take 2-3 mL, add about 2 mL 10% NaOH and a few drops copper reagent, warm about five minutes.","Violet colour supports a protein response.",q("protein stock aliquot",(2,3),"mL",concentration="0.5% w/v in 0.1 M NaOH"),q("NaOH",2,"mL",qualifier="approximate",concentration="10% (basis not stated)"),q("copper reagent",note="Few drops."))
    food("ninhydrin","Protein / ninhydrin",10,"Use 2-3 mL aqueous albumin and 3-4 drops ninhydrin; heat.","Blue colour is a positive response.",q("albumin solution",(2,3),"mL"),q("ninhydrin",(3,4),"drops"))
    food("xanthoproteic","Protein / xanthoproteic",10,"Use 1 mL aqueous albumin with a few drops concentrated nitric acid; heat for a few minutes, cool under the tap and add a few drops 10 M NaOH.","Yellow changes to orange after alkali addition for the source sample.",q("albumin solution",1,"mL"),q("conc HNO3",note="Few drops."),q("NaOH",concentration="10 M",note="Few drops."))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir",type=Path,default=Path.home()/"Downloads")
    args=parser.parse_args()
    reference_path=ROOT/"data/quantity_source_manifest.json"
    expected={entry["file"]: entry["sha256"] for entry in json.loads(reference_path.read_text(encoding="utf-8"))["sources"]} if reference_path.exists() else {}
    manifest=[]
    for n in range(101,112):
        path=args.source_dir/f"lelm{n}.pdf"
        manifest.append({"source_id":f"ncert_lelm{n}","file":path.name,
                         "pdf_pages": [7,11,11,4,6,9,37,14,4,10,11][n-101],
                         "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                         "url":f"https://ncert.nic.in/pdf/publication/sciencelaboratorymanuals/classXII/chemistry/lelm{n}.pdf"})
        if expected and expected.get(path.name)!=manifest[-1]["sha256"]:
            raise ValueError(f"{path.name} differs from the transcribed source. Review the changed PDF before applying these curated facts.")
    curate()
    target=ROOT/"data/chemistry_experiments.json"
    payload=json.loads(target.read_text(encoding="utf-8"))
    report=[]
    for record in payload["experiments"]:
        rid=record["experiment_id"]
        previous_review=record.get("quantity_review",{})
        variants=PROTOCOLS.get(rid,[])
        gaps=["No vessel safe-working volume or calibrated drop-to-mL conversion has been inferred."]
        coverage="transcribed" if variants else "not_covered"
        if rid in ("chem_12_301","chem_12_402","chem_12_403","chem_12_801"):
            coverage="partial"
            gaps.append("Selected test/preparation branches are transcribed; aggregate entry is not an exhaustive executable protocol. Untranscribed branches require source review.")
        if not variants:
            gaps=["The supplied Class XII chemistry units do not specify this record's complete procedure and doses; original values are unchanged."]
            if record["subject"]=="Physics":
                gaps=["Physics is outside the supplied chemistry manuals; no quantity changes made."]
            if rid=="chem_12_201":
                coverage="cross_reference_only"
                gaps=["lelm106.pdf p3 references Class XI Unit 2 Experiment 2.1 for 0.1 M oxalic acid; preparation mass and batch volume are not given in the supplied PDF."]
            if rid=="chem_12_607":
                coverage="related_test_only"
                gaps=["lelm108.pdf p4 contains diagnostic iodoform tests, not this preparative experiment. See chem_12_402 variants; no scale substitution made."]
        review={"date":"2026-10-22","coverage":coverage,
                "source_ids":sorted({v["source_id"] for v in variants}),
                "requires_protocol_selection":len(variants)>1,
                "numeric_completeness":"not_certified",
                "gaps":gaps,
                "policy":"Ranges, approximations, stock amounts, final volumes, capacities, ratios and endpoint additions retain their distinct meanings. Unstated amounts remain absent. Transcription is not scientific approval."}
        record["quantity_review"]=review
        if variants:
            record.setdefault("legacy_procedure_steps",record["procedure_steps"])
            record.setdefault("legacy_materials",record["materials"])
            record.setdefault("legacy_scenes",record["scenes"])
            record["materials"]=MATERIALS[rid.rsplit("_",1)[1]]
            record["protocol_variants"]=variants
            record["selected_protocol_variant"]=None if len(variants)>1 else variants[0]["variant_id"]
            if len(variants)==1 and len(variants[0]["procedure_steps"])>=3:
                record["procedure_steps"]=variants[0]["procedure_steps"]
            else:
                record["procedure_steps"]=[
                    {"step_id":1,"instruction":"Select one source-backed protocol variant and identify its sample and reagents before rendering.","observation":"This catalogue overview is not an executable combined procedure."},
                    {"step_id":2,"instruction":"Resolve unspecified doses, source conflicts and sample/reference-image requirements for the selected variant.","observation":"Unknown quantities remain unset; alternatives and fresh aliquots remain separate."},
                    {"step_id":3,"instruction":"Use only the selected variant's source-evidenced steps after scientific review.","observation":"Do not concatenate the alternative tests into one vessel or invent a universal positive outcome."}]
            # Put the supplied source first; preserve old microscale sources as legacy context.
            new_sources=[]
            for entry in manifest:
                if entry["source_id"] in review["source_ids"]:
                    pages=sorted({e["pdf_page"] for v in variants for st in v["procedure_steps"] for e in st["source_evidence"] if e["source_id"]==entry["source_id"]})
                    new_sources.append({"source_id":entry["source_id"],"source_type":"ncert_lab_manual","url":entry["url"],"citation":f"User-supplied NCERT XII Chemistry {entry['file']}; PDF pages {', '.join(map(str,pages))} (1-based). File SHA-256 in data/quantity_source_manifest.json.","verification_status":"verified"})
            record["sources"]=new_sources+[x for x in record["sources"] if x["source_id"] not in review["source_ids"]]
        if rid=="chem_12_205":
            review["previous_title"]=previous_review.get("previous_title",record["title"])
            record["title"]="Determine the molarity of potassium permanganate using 0.1 M oxalic acid"
        if variants:
            record["scenes"]=[{"scene_id":"selected_protocol","name":"Selected source-backed protocol",
                "description":f"A fixed educational view of {record['title']}. Prepare only the apparatus and starting state for the selected protocol and its identified sample; use its supplied NCERT source, not legacy microscale staging.",
                "visible_actions":["perform the selected protocol's reviewed source-evidenced steps"],
                "image_asset_id":record["image_assets"][0]["image_asset_id"]}]
            record.setdefault("legacy_educational_goal",record["educational_goal"])
            record["educational_goal"]=f"Study '{record['title']}' using a selected NCERT XII chemistry protocol, its documented quantities and conditions, and conditional observations; review unresolved doses before rendering."
        report.append({"experiment_id":rid,"title":record["title"],"coverage":coverage,"variants":len(variants),"gaps":gaps})
    payload["dataset_version"]="0.4.0"
    target.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (ROOT/"data/quantity_source_manifest.json").write_text(json.dumps({"date":"2026-10-22","page_numbering":"1-based PDF page, not printed folio","sources":manifest},indent=2)+"\n",encoding="utf-8")
    counts=dict(Counter(r["coverage"] for r in report))
    (ROOT/"data/quantity_coverage_audit.json").write_text(json.dumps({"counts":counts,"records":report},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    report_path=ROOT/"QUANTITY_REVIEW.md"
    if report_path.exists():
        heading="The following inventory is generated from the canonical coverage audit."
        prefix=report_path.read_text(encoding="utf-8").split(heading)[0]+heading
        table="\n\n| Record | Experiment | Coverage | Variants |\n| --- | --- | --- | --- |\n"
        table+="\n".join(f"| {r['experiment_id']} | {r['title']} | {r['coverage']} | {r['variants']} |" for r in report)+"\n"
        report_path.write_text(prefix+table,encoding="utf-8")
    print(json.dumps({"records_audited":len(report),"protocol_records":len(PROTOCOLS),"variants":sum(map(len,PROTOCOLS.values())),"coverage":counts}))


if __name__=="__main__":
    main()
